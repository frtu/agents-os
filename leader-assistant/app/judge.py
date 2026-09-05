"""Layer 3 — the checker: an LLM risk agent behind a deterministic grant filter.

The judge answers one question — must the operator be asked about this run? — and answers it with
a model, because novel shapes are exactly what a fixed rule table cannot weigh (spec 011 FR-15/
FR-16). Its reasoning is recorded verbatim on the verdict: it *is* the audit justification for
whatever happens next (FR-16, AC-19).

**The model judges; code grants (D4).** A model can always be argued into less friction, so its
answer is only ever a *recommendation*. Every recommendation passes through ``apply_filter`` — a
pure, synchronous function with no model in it — which alone decides whether the recommendation is
honoured (FR-17..FR-21). Nothing the model emits can select the verdict's ``source``, set
``matched_precedent``, or reach around the filter; the filter's inputs are the operator's trust
mode, recorded precedent and the report's score, none of which the model supplies. This is
Constitution P8 v2.0.0's "the grant is issued by code after the checker speaks".

**The judge cannot act (FR-22, AC-11).** It imports no capability layer, registers no tools, is
given none by the SDK call, and writes no file — not even the experience store, which is the
concierge's business. Its blast radius if wholly compromised is bounded to *asking more*: the
filter's failure direction is always ``ask`` (FR-19/FR-21).

Import direction (FR-34): ``config`` for thresholds and ``workflow`` for the FR-13 contract, and
nothing else from this app. Precedent arrives as an *input* — the judge never goes looking for it,
so ``experience`` stays replaceable (FR-35).
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Awaitable, Callable

from . import config, tracing
from .workflow import DECISIONS, RiskReport, Verdict, control_mode_verdict

# The model call is on the operator's critical path: a turn is paused while it runs. A judge that
# hangs must degrade to a card, not to a spinner (FR-21).
JUDGE_TIMEOUT_SECONDS = 30.0

# `source` values this module can produce. `filter` marks a verdict deterministic code chose over
# the model's — the audit record needs to distinguish "the judge said ask" from "the judge was
# overruled".
SOURCES = ("judge", "trust", "precedent", "filter", "control-mode-off")


class JudgeUnavailable(RuntimeError):
    """The risk agent could not be reached; the filter resolves this to ``ask`` (spec 011 FR-21)."""


JUDGE_SYSTEM_PROMPT = """\
You are the risk checker for a local knowledge assistant. You do not perform work and you have no
tools; you assess an execution that has been paused mid-flight and recommend what should happen.

You are given the operator's objective, the operations already executed in this run, and the
operation that has just tripped the risk gate. Each operation carries a 1-5 risk score, the
modifiers that produced it, and a one-line statement of its effect and undo path.

Recommend exactly one decision:
  approve - the accumulated blast radius is proportionate to the stated objective and recoverable.
  decline - the operation should not run at all.
  ask     - the operator should decide.

Judge the *effect*, not the phrasing of the objective. Weigh what has already happened, not only
the gating operation. Prefer "ask" whenever the objective does not clearly entail the effect.

Your recommendation is advisory: a deterministic filter decides whether it is honoured, and cannot
be influenced by anything you write. Your reasoning is kept verbatim as the audit record of this
decision, so make it a factual account of the effect you weighed - one or two sentences.

Reply with ONLY a JSON object, no prose and no code fence:
{"decision": "approve|decline|ask", "reasoning": "<one or two sentences>", "confidence": 0.0-1.0}
"""


@dataclass(frozen=True)
class Precedent:
    """What recorded experience says about one operation shape (spec 011 FR-17/D5).

    Deliberately declared here rather than imported from ``experience``: the judge consumes
    precedent as plain data supplied by its caller, which is what keeps the two layers separately
    testable and replaceable (FR-34/FR-35). Counts are already window-filtered by whoever looked
    the precedent up — this module does no date arithmetic.
    """

    precedent_id: str
    fingerprint: str
    approvals: int = 0
    declines: int = 0
    last_decision: str = ""

    def unlocks_skip(self, min_samples: int) -> bool:
        """Enough operator approvals, and no operator decline in the window (FR-17).

        A single decline disqualifies the shape outright rather than being outvoted by approvals:
        consent must not be reachable by averaging (P8 — a checker may learn to ask less, never to
        assume more).
        """
        return self.approvals >= min_samples and self.declines == 0

    def holds_decline(self) -> bool:
        """Does this shape carry a prior *operator* refusal (FR-19)?"""
        return self.declines > 0


@dataclass(frozen=True)
class Recommendation:
    """The model's advisory answer, before the filter (spec 011 D4)."""

    decision: str
    reasoning: str
    confidence: float = 0.0


# (system_prompt, user_prompt) -> raw model text. Injectable so the judge is testable, and the
# whole layer runnable, with no `claude` CLI present (FR-35).
AskModel = Callable[[str, str], Awaitable[str]]


def build_prompt(report: RiskReport, trust: bool) -> str:
    """Render the report for the model (spec 011 FR-15).

    Carries the objective, everything already executed, and the gating operation — the same blast
    radius the operator would be shown (FR-11), so judge and operator reason over one picture.
    The trust hint is stated as the operator's *standing posture*, never as permission: the model
    is told plainly that it does not decide whether that posture applies.
    """
    lines = [
        f"OBJECTIVE: {report.objective}",
        f"WORKSPACE: {report.workspace}",
        f"RUN: {report.run_id}",
        "",
        f"OPERATOR HINT: standing consent (trust mode) is {'ON' if trust else 'OFF'}. "
        "This is context only; whether it authorises anything is decided after you answer.",
        "",
        "ALREADY EXECUTED IN THIS RUN:",
    ]
    executed = [s for s in report.accumulated if s.status == "executed"]
    if executed:
        lines.extend(_render_op(s) for s in executed)
    else:
        lines.append("  (nothing)")

    others = [
        s for s in report.accumulated
        if s.status != "executed" and s.operation.op_id != report.gating.operation.op_id
    ]
    if others:
        lines.append("")
        lines.append("ALSO RECORDED ON THIS RUN:")
        lines.extend(_render_op(s) for s in others)

    lines.extend(
        [
            "",
            "GATING OPERATION (paused, not yet run):",
            _render_op(report.gating),
            "",
            f"HIGHEST SCORE IN THIS RUN: {report.max_score}",
            "",
            "Answer with the JSON object only.",
        ]
    )
    return "\n".join(lines)


def _render_op(scored) -> str:
    op = scored.operation
    mods = ", ".join(scored.modifiers) or "none"
    external = "yes" if op.external else "no"
    return (
        f"  - [{scored.score}] {op.kind}:{op.name} -> {op.target or '(no target)'}\n"
        f"      tier={op.tier} status={scored.status} external={external} modifiers={mods}\n"
        f"      effect: {scored.justification}\n"
        f"      undo: {op.reversibility}"
    )


def parse_recommendation(raw: str) -> Recommendation | None:
    """Parse the model's JSON, returning ``None`` on anything unusable (spec 011 FR-21).

    Every rejection here becomes an ``ask``: a judge that cannot state its answer in the agreed
    shape has not answered. Tolerates a code fence and surrounding chatter, because that is
    cosmetic; does not tolerate a decision outside the vocabulary, because that is not.
    """
    if not isinstance(raw, str):
        return None
    body = _extract_object(raw)
    if body is None:
        return None
    try:
        data = json.loads(body)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    decision = data.get("decision")
    if not isinstance(decision, str) or decision.strip().lower() not in DECISIONS:
        return None
    reasoning = data.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        return None
    return Recommendation(
        decision=decision.strip().lower(),
        reasoning=reasoning.strip(),
        confidence=_confidence(data.get("confidence")),
    )


def _extract_object(raw: str) -> str | None:
    """First balanced ``{...}`` in the text, so a stray preamble does not cost a verdict."""
    start = raw.find("{")
    if start < 0:
        return None
    depth, in_string, escaped = 0, False, False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    return None


def _confidence(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


# Reasons the filter records when it overrules the model. Kept as constants so the audit record and
# the tests agree on the wording an operator will read.
FAIL_CLOSED_REASON = "the judge was unavailable or its answer was malformed; asking is the safe default"
JUDGE_DOWN_PASSTHROUGH_REASON = (
    "the judge was unavailable or its answer was malformed, but this operation is reversible "
    "(git-recoverable) and at or below the judge-unavailable safe ceiling, so it runs and is "
    "recorded for revert rather than deadlocking the run"
)
COLD_START_REASON = "no recorded experience yet, so no shape has precedent; asking is the safe default"
NO_AUTHORITY_REASON = (
    "neither standing consent nor a matching precedent authorises skipping the ask, "
    "so the approve recommendation is not honoured"
)
CEILING_REASON_TEMPLATE = (
    "score {score} exceeds the precedent-free ceiling of {ceiling} and no matching precedent "
    "exists, so standing consent alone cannot authorise it"
)
NO_DECLINE_PRECEDENT_REASON = (
    "a decline is only autonomous on the precedent of a prior operator decline for this shape, "
    "and there is none; the judge may not invent a refusal"
)


def apply_filter(
    recommendation: Recommendation | None,
    *,
    trust: bool,
    precedent: Precedent | None,
    experience_empty: bool,
    max_score: int,
    ceiling: int,
    min_samples: int,
    reversible: bool = False,
    judge_down_ceiling: int = 0,
) -> Verdict:
    """Turn a recommendation into a verdict — the FR-17..FR-21/FR-44 grant filter (spec 011 D4).

    Pure and synchronous by design: no model, no I/O, no clock. The model's recommendation enters
    only as ``recommendation``; the authority to honour it comes exclusively from the other
    arguments, none of which the model can set. Every path that is not an outright honour resolves
    to ``ask`` — the filter has no failure mode that grants, save the one bounded passthrough of
    FR-44, which fires *only* when the model is silent and never widens with anything the model said.

    A downgrade keeps the model's reasoning **verbatim** and appends why it was overruled: an
    operator auditing the record needs the judgment *and* the reason it did not stand (FR-16).
    """
    if recommendation is None:
        # FR-44: a dead checker must not deadlock low-risk, git-recoverable work. A reversible-tier
        # operation at or below the judge-unavailable ceiling auto-runs (recorded, revertible);
        # approval-tier executable actions and anything above the ceiling still fail closed to ask.
        if reversible and max_score <= judge_down_ceiling:
            return Verdict(
                decision="approve", reasoning=JUDGE_DOWN_PASSTHROUGH_REASON, source="filter"
            )
        return Verdict(decision="ask", reasoning=FAIL_CLOSED_REASON, source="filter")

    # FR-20 cold start: with nothing recorded, no shape can have precedent, so nothing is
    # delegable — including under standing consent, whose scope is what experience defines.
    if experience_empty:
        return _downgrade(recommendation, COLD_START_REASON)

    if recommendation.decision == "ask":
        return _honour(recommendation, source="judge")

    if recommendation.decision == "decline":
        # FR-19 / D8: the system may learn to stop asking; it may never learn to start refusing.
        if precedent is not None and precedent.holds_decline():
            return _honour(recommendation, source="precedent", precedent=precedent)
        return _downgrade(recommendation, NO_DECLINE_PRECEDENT_REASON)

    unlocking = precedent if precedent is not None and precedent.unlocks_skip(min_samples) else None

    # FR-18: the ceiling binds standing consent too. Only a precedent strong enough to unlock a
    # skip on its own lifts it — a shape seen once is not evidence at score 5.
    if max_score > ceiling and unlocking is None:
        return _downgrade(
            recommendation, CEILING_REASON_TEMPLATE.format(score=max_score, ceiling=ceiling)
        )

    # FR-17 bounded delegation. Standing consent is named first when both apply: it is the
    # operator's live, revocable instrument, and the record should say so.
    if trust:
        return _honour(recommendation, source="trust", precedent=unlocking)
    if unlocking is not None:
        return _honour(recommendation, source="precedent", precedent=unlocking)
    return _downgrade(recommendation, NO_AUTHORITY_REASON)


def _honour(
    rec: Recommendation, *, source: str, precedent: Precedent | None = None
) -> Verdict:
    return Verdict(
        decision=rec.decision,
        reasoning=rec.reasoning,
        confidence=rec.confidence,
        source=source,
        matched_precedent=precedent.precedent_id if precedent is not None else None,
    )


def _downgrade(rec: Recommendation, why: str) -> Verdict:
    """Overrule a recommendation, preserving it for the audit record (spec 011 FR-16/FR-17)."""
    return Verdict(
        decision="ask",
        reasoning=(
            f"{rec.reasoning}\n\n[filter] judge recommended {rec.decision}; "
            f"downgraded to ask because {why}."
        ),
        confidence=rec.confidence,
        source="filter",
    )


class Judge:
    """The FR-13 checker, implemented as an LLM risk agent (spec 011 FR-15/FR-16).

    Holds no state a run could pollute and no path to execution (FR-22). Thresholds are read from
    ``config`` at review time, not at construction, so a hand-edit of the weights file takes effect
    on the next decision (FR-32, AC-18).
    """

    def __init__(
        self,
        *,
        trust: bool,
        precedent_lookup: Callable[[RiskReport], Precedent | None],
        experience_empty: Callable[[], bool],
        ask_model: AskModel | None = None,
        timeout: float = JUDGE_TIMEOUT_SECONDS,
    ) -> None:
        self._trust = trust
        self._precedent_lookup = precedent_lookup
        self._experience_empty = experience_empty
        self._ask_model = ask_model or sdk_ask_model
        self._timeout = timeout

    async def review(self, report: RiskReport) -> Verdict:
        """Recommend with the model, then grant with code (spec 011 FR-15..FR-21)."""
        # spec 013 FR-5: control mode off bypasses this layer entirely - no model call and no
        # filter. Deliberately *before* ``_recommend`` so the LLM is neither paid for nor waited
        # on: "turn off all LLM checks" must mean the call does not happen, not that its answer
        # is discarded.
        if not config.control_mode():
            return control_mode_verdict()
        recommendation = await self._recommend(report)
        return apply_filter(
            recommendation,
            trust=self._trust,
            precedent=self._safe(lambda: self._precedent_lookup(report), None),
            # A lookup that cannot tell us the store is populated is treated as cold (FR-20/FR-21).
            experience_empty=self._safe(self._experience_empty, True),
            max_score=report.max_score,
            ceiling=config.precedent_free_ceiling(),
            min_samples=config.precedent_min_samples(),
            # FR-44: only a git-recoverable mutation may auto-run under a dead judge; an
            # approval-tier executable action still waits for a human.
            reversible=report.gating.operation.tier != "approval",
            judge_down_ceiling=config.judge_unavailable_safe_ceiling(),
        )

    async def _recommend(self, report: RiskReport) -> Recommendation | None:
        """Single-shot model call. Returns ``None`` for every failure mode (spec 011 FR-21)."""
        try:
            raw = await asyncio.wait_for(
                self._ask_model(JUDGE_SYSTEM_PROMPT, build_prompt(report, self._trust)),
                timeout=self._timeout,
            )
        except Exception:  # noqa: BLE001 — no judge failure may open the gate; covers the timeout
            return None
        return parse_recommendation(raw)

    @staticmethod
    def _safe(fn, fallback):
        """Run a caller-supplied lookup, falling back to the closed answer if it raises (FR-21)."""
        try:
            return fn()
        except Exception:  # noqa: BLE001
            return fallback


async def sdk_ask_model(system_prompt: str, prompt: str) -> str:
    """One stateless model call with **no tools** (spec 011 FR-16/FR-22).

    Deliberately not routed through ``agent.run_stream``: that runtime exists to *do work* — it
    mounts the capability MCP server, grants native tools and runs under ``bypassPermissions``.
    The judge must be unable to act, so it gets its own call with an empty tool set, no MCP
    server, no settings sources (which would load skills) and a single turn. Import-guarded and
    exception-mapped like ``agent``, so a missing ``claude`` CLI surfaces as a failure the filter
    can fail closed on rather than a crash.
    """
    try:
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            TextBlock,
            query,
        )
    except ImportError as e:  # pragma: no cover — no SDK installed
        raise JudgeUnavailable(str(e)) from e

    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=config.judge_model(),
        allowed_tools=[],
        mcp_servers={},
        setting_sources=[],
        max_turns=1,
    )
    text = ""
    with tracing.generation("judge-review", model=config.judge_model(), input=prompt) as gen:
        try:  # pragma: no cover — requires the claude CLI
            async for message in query(prompt=prompt, options=opts):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text += block.text
        except Exception as e:  # noqa: BLE001 — mapped, never leaked as an SDK type
            raise JudgeUnavailable(str(e)) from e
        gen.update(output=text)
    return text
