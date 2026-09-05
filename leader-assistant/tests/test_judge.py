"""Feature 011 layer 3 — the checker (spec 011 FR-15..FR-22; AC-8..AC-13).

The theme: **the model judges, code grants** (spec 011 D4). Every test drives the real `Judge`
with a fake `ask_model`, so what is being pinned is never the model's opinion but what the
deterministic filter *does* with it. No test needs the `claude` CLI or a live LLM.

The recurring assertion is asymmetric on purpose: a recommendation can only ever be honoured or
downgraded to `ask`. There is no input — from the model or otherwise — that widens authority.
"""

from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path

import pytest

from app import judge
from app.execution_gate import Operation
from app.workflow import Checker, RiskReport, ScoredOperation

# Modules layer 3 must never reach: they either execute work or belong to another layer (FR-22/FR-34).
FORBIDDEN_IMPORTS = {"capabilities", "experience", "concierge", "vault", "agent", "api", "ui"}


def _scored(score: int, *, name: str = "import_skill", status: str = "pending") -> ScoredOperation:
    return ScoredOperation(
        operation=Operation(
            kind="capability",
            name=name,
            target="weekly-digest",
            tier="approval",
            reversibility="revert the workspace git commit",
        ),
        score=score,
        modifiers=("PRIVILEGE_GRANTING",),
        justification=f"{name} on weekly-digest; recoverable from the workspace git repo",
        status=status,
    )


def _report(score: int = 4, *, executed: int = 0) -> RiskReport:
    gating = _scored(score)
    prior = tuple(_scored(2, name="ingest", status="executed") for _ in range(executed))
    return RiskReport(
        run_id="run-1",
        objective="install the weekly-digest skill",
        workspace="demo",
        gating=gating,
        accumulated=(*prior, gating),
    )


def _model(decision: str, reasoning: str = "The effect is one reference-link, reversible via git.",
           confidence: float = 0.8):
    """A fake model that answers in the agreed JSON shape."""

    async def ask_model(_system: str, _prompt: str) -> str:
        return json.dumps({"decision": decision, "reasoning": reasoning, "confidence": confidence})

    return ask_model


def _judge(
    decision: str = "approve",
    *,
    trust: bool = False,
    precedent: judge.Precedent | None = None,
    empty: bool = False,
    ask_model=None,
    reasoning: str = "The effect is one reference-link, reversible via git.",
    timeout: float = judge.JUDGE_TIMEOUT_SECONDS,
) -> judge.Judge:
    return judge.Judge(
        trust=trust,
        precedent_lookup=lambda _report: precedent,
        experience_empty=lambda: empty,
        ask_model=ask_model or _model(decision, reasoning),
        timeout=timeout,
    )


def _review(j: judge.Judge, report: RiskReport | None = None):
    return asyncio.run(j.review(report if report is not None else _report()))


def _precedent(approvals: int = 5, declines: int = 0, last: str = "approve") -> judge.Precedent:
    return judge.Precedent(
        precedent_id="prec-abc123",
        fingerprint="capability:import_skill:weekly-digest",
        approvals=approvals,
        declines=declines,
        last_decision=last,
    )


# --- FR-17 bounded delegation -------------------------------------------------------------------

def test_approve_without_trust_or_precedent_is_downgraded_fr17_ac8():
    """A judge approve with neither standing consent nor precedent asks (spec 011 FR-17, AC-8)."""
    verdict = _review(_judge("approve"))
    assert verdict.decision == "ask"
    assert verdict.source == "filter"
    assert verdict.matched_precedent is None


def test_approve_under_trust_is_honoured_fr17():
    """Standing consent is one of the two grants the filter recognises (spec 011 FR-17)."""
    verdict = _review(_judge("approve", trust=True))
    assert verdict.decision == "approve"
    assert verdict.source == "trust"


def test_approve_on_sufficient_precedent_is_honoured_fr17_ac12():
    """Repeated operator approvals of the same shape unlock the skip (spec 011 FR-17, AC-12)."""
    verdict = _review(_judge("approve", precedent=_precedent(approvals=5)))
    assert verdict.decision == "approve"
    assert verdict.source == "precedent"
    assert verdict.matched_precedent == "prec-abc123"


def test_decline_in_window_disqualifies_precedent_fr17():
    """One operator decline in the window revokes the shape's precedent (spec 011 FR-17)."""
    verdict = _review(_judge("approve", precedent=_precedent(approvals=9, declines=1)))
    assert verdict.decision == "ask"
    assert verdict.source == "filter"


def test_precedent_below_min_samples_does_not_unlock_fr17(monkeypatch):
    """Precedent must meet the configured sample count, not merely exist (spec 011 FR-17)."""
    monkeypatch.setenv("LEADER_PRECEDENT_MIN_SAMPLES", "3")
    verdict = _review(_judge("approve", precedent=_precedent(approvals=2)))
    assert verdict.decision == "ask"
    assert verdict.source == "filter"


def test_thresholds_are_read_at_review_time_fr17(monkeypatch):
    """A hand-edited threshold binds the next decision, not the next process (spec 011 FR-32)."""
    j = _judge("approve", precedent=_precedent(approvals=2))
    monkeypatch.setenv("LEADER_PRECEDENT_MIN_SAMPLES", "2")
    assert _review(j).decision == "approve"


def test_downgrade_preserves_reasoning_and_explains_itself_fr17():
    """An audit record needs both the judgment and why it did not stand (spec 011 FR-16/FR-17)."""
    reasoning = "Only one link is created and git can revert it."
    verdict = _review(_judge("approve", reasoning=reasoning))
    assert reasoning in verdict.reasoning
    assert "downgraded to ask" in verdict.reasoning
    assert judge.NO_AUTHORITY_REASON in verdict.reasoning


# --- FR-18 precedent-free ceiling ---------------------------------------------------------------

def test_above_ceiling_without_precedent_asks_even_under_trust_fr18(monkeypatch):
    """Novel work still asks in trust mode (spec 011 FR-18; scenario 4)."""
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "4")
    verdict = _review(_judge("approve", trust=True), _report(score=5))
    assert verdict.decision == "ask"
    assert verdict.source == "filter"
    assert "precedent-free ceiling" in verdict.reasoning


def test_above_ceiling_with_precedent_is_honoured_fr18(monkeypatch):
    """The ceiling is lifted by precedent, which is exactly what it is a ceiling on (FR-18)."""
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "4")
    verdict = _review(_judge("approve", trust=True, precedent=_precedent(approvals=5)), _report(5))
    assert verdict.decision == "approve"


def test_ceiling_uses_the_reports_max_score_not_the_gating_op_fr18(monkeypatch):
    """The blast radius is the whole run, so the ceiling is judged on its peak (FR-11/FR-18)."""
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "4")
    gating = _scored(4)
    report = RiskReport(
        run_id="run-2",
        objective="reorganise the wiki",
        workspace="demo",
        gating=gating,
        accumulated=(_scored(5, name="Bash", status="executed"), gating),
    )
    assert _review(_judge("approve", trust=True), report).decision == "ask"


# --- FR-19 decline never generalises ------------------------------------------------------------

def test_decline_without_precedent_is_downgraded_fr19_ac13():
    """The judge may not invent a refusal (spec 011 FR-19, AC-13)."""
    verdict = _review(_judge("decline"))
    assert verdict.decision == "ask"
    assert verdict.source == "filter"
    assert judge.NO_DECLINE_PRECEDENT_REASON in verdict.reasoning


def test_decline_without_precedent_is_downgraded_even_under_trust_fr19():
    """Standing consent authorises less friction, never a refusal (spec 011 FR-19/D8)."""
    assert _review(_judge("decline", trust=True)).decision == "ask"


def test_decline_on_operator_decline_precedent_is_honoured_fr19():
    """A recorded operator refusal of the same shape is the only autonomous decline (FR-19)."""
    verdict = _review(_judge("decline", precedent=_precedent(approvals=0, declines=2, last="decline")))
    assert verdict.decision == "decline"
    assert verdict.source == "precedent"
    assert verdict.matched_precedent == "prec-abc123"


# --- FR-20 cold start ---------------------------------------------------------------------------

def test_empty_experience_store_always_asks_fr20_ac9():
    """A fresh install asks whatever the judge reasons (spec 011 FR-20, AC-9)."""
    for trust in (False, True):
        verdict = _review(_judge("approve", trust=trust, empty=True, precedent=_precedent()))
        assert verdict.decision == "ask"
        assert verdict.source == "filter"
        assert judge.COLD_START_REASON in verdict.reasoning


def test_cold_start_also_blocks_an_autonomous_decline_fr20():
    """Cold start is a blanket ask, in both directions (spec 011 FR-19/FR-20)."""
    assert _review(_judge("decline", empty=True)).decision == "ask"


# --- FR-21 fail closed --------------------------------------------------------------------------

def test_unavailable_judge_asks_fr21_ac10():
    """An unreachable risk agent resolves to ask (spec 011 FR-21, AC-10; scenario 7)."""

    async def boom(_system, _prompt):
        raise judge.JudgeUnavailable("claude CLI not found")

    verdict = _review(_judge(ask_model=boom))
    assert verdict.decision == "ask"
    assert verdict.source == "filter"
    assert verdict.reasoning == judge.FAIL_CLOSED_REASON


def test_timed_out_judge_asks_fr21_ac10():
    """A hung judge becomes a card, not a spinner (spec 011 FR-21, AC-10)."""

    async def slow(_system, _prompt):
        await asyncio.sleep(5)
        return json.dumps({"decision": "approve", "reasoning": "fine", "confidence": 1.0})

    verdict = _review(_judge(ask_model=slow, trust=True, timeout=0.01))
    assert verdict.decision == "ask"
    assert verdict.reasoning == judge.FAIL_CLOSED_REASON


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "I think this is probably fine, go ahead.",
        "{not json at all",
        json.dumps({"reasoning": "no decision field"}),
        json.dumps({"decision": "approve"}),  # no reasoning to audit
        json.dumps({"decision": "yolo", "reasoning": "outside the vocabulary"}),
        json.dumps({"decision": "APPROVE_ALWAYS", "reasoning": "widening itself"}),
        json.dumps(["approve"]),
    ],
)
def test_malformed_judge_response_asks_fr21_ac10(raw):
    """Anything not a well-formed decision is not a decision (spec 011 FR-21, AC-10)."""

    async def garbage(_system, _prompt):
        return raw

    verdict = _review(_judge(ask_model=garbage, trust=True))
    assert verdict.decision == "ask"
    assert verdict.reasoning == judge.FAIL_CLOSED_REASON


def test_fenced_json_is_still_parsed_fr21():
    """A code fence is cosmetic; only the decision itself is load-bearing (spec 011 FR-21)."""

    async def fenced(_system, _prompt):
        return '```json\n{"decision": "approve", "reasoning": "reversible", "confidence": 0.5}\n```'

    assert _review(_judge(ask_model=fenced, trust=True)).decision == "approve"


def test_a_raising_precedent_lookup_fails_closed_fr21():
    """A broken experience store may not open the gate (spec 011 FR-21)."""

    def boom(_report):
        raise OSError("experience store unreadable")

    j = judge.Judge(
        trust=False,
        precedent_lookup=boom,
        experience_empty=lambda: False,
        ask_model=_model("approve"),
    )
    assert _review(j).decision == "ask"


def test_a_raising_emptiness_check_is_treated_as_cold_fr21():
    """Unable to prove experience exists is the same as having none (spec 011 FR-20/FR-21)."""

    def boom():
        raise OSError("experience store unreadable")

    j = judge.Judge(
        trust=True,
        precedent_lookup=lambda _r: _precedent(),
        experience_empty=boom,
        ask_model=_model("approve"),
    )
    assert _review(j).decision == "ask"


# --- FR-44 judge-unavailable passthrough --------------------------------------------------------

def _reversible_report(score: int) -> RiskReport:
    """A reversible-tier gating report at a chosen score — the shape FR-44 may let through."""
    op = ScoredOperation(
        operation=Operation(
            kind="tool",
            name="Write",
            target="vault/wiki/portal.md",
            tier="reversible",
            reversibility="git revert the turn commit",
        ),
        score=score,
        modifiers=(),
        justification="rewrite one wiki page; recoverable from the workspace git repo",
    )
    return RiskReport(
        run_id="run-1", objective="rewrite wiki pages", workspace="demo", gating=op, accumulated=(op,)
    )


def test_judge_down_lets_reversible_low_risk_through_fr44_ac29():
    """A dead judge does not deadlock a reversible op at/under the ceiling (spec 011 FR-44, AC-29)."""

    async def boom(_system, _prompt):
        raise judge.JudgeUnavailable("claude CLI not found")

    verdict = _review(_judge(ask_model=boom), report=_reversible_report(4))
    assert verdict.decision == "approve"
    assert verdict.source == "filter"
    assert verdict.reasoning == judge.JUDGE_DOWN_PASSTHROUGH_REASON
    # AC-29: a passthrough is a filter grant, never operator precedent.
    assert verdict.matched_precedent is None


def test_judge_down_still_asks_for_approval_tier_fr44_ac30():
    """The escape is reversible-only; an approval-tier executable still fails closed (FR-44, AC-30)."""

    async def boom(_system, _prompt):
        raise judge.JudgeUnavailable("claude CLI not found")

    # The default _report() is approval-tier, so it must keep asking even at the ceiling score.
    verdict = _review(_judge(ask_model=boom), report=_report(4))
    assert verdict.decision == "ask"
    assert verdict.reasoning == judge.FAIL_CLOSED_REASON


def test_judge_down_still_asks_above_the_ceiling_fr44_ac30():
    """A reversible op scoring above the ceiling is not "not too risky" — it asks (FR-44, AC-30)."""

    async def boom(_system, _prompt):
        raise judge.JudgeUnavailable("claude CLI not found")

    verdict = _review(_judge(ask_model=boom), report=_reversible_report(5))
    assert verdict.decision == "ask"
    assert verdict.reasoning == judge.FAIL_CLOSED_REASON


def test_a_timed_out_judge_also_lets_reversible_low_risk_through_fr44():
    """Timeout is one flavour of "judge silent"; the same passthrough applies (spec 011 FR-44)."""

    async def slow(_system, _prompt):
        await asyncio.sleep(5)
        return json.dumps({"decision": "approve", "reasoning": "fine", "confidence": 1.0})

    verdict = _review(_judge(ask_model=slow, timeout=0.01), report=_reversible_report(4))
    assert verdict.decision == "approve"
    assert verdict.source == "filter"


def test_ceiling_below_gate_restores_pure_fail_closed_fr44_ac30(monkeypatch):
    """The ceiling is data: set it under the gate and FR-44 stops firing entirely (FR-44, AC-30)."""
    monkeypatch.setenv("LEADER_JUDGE_UNAVAILABLE_SAFE_CEILING", "3")

    async def boom(_system, _prompt):
        raise judge.JudgeUnavailable("claude CLI not found")

    verdict = _review(_judge(ask_model=boom), report=_reversible_report(4))
    assert verdict.decision == "ask"
    assert verdict.reasoning == judge.FAIL_CLOSED_REASON


def test_the_passthrough_never_widens_on_what_the_model_said_fr44():
    """Even a malformed "approve" is silence; the grant comes from tier+score, not the payload."""

    async def garbage(_system, _prompt):
        return json.dumps({"decision": "APPROVE_ALWAYS", "reasoning": "widening itself"})

    # Malformed → recommendation None → passthrough decides purely on reversible+score.
    approved = _review(_judge(ask_model=garbage), report=_reversible_report(4))
    assert approved.decision == "approve"
    assert approved.reasoning == judge.JUDGE_DOWN_PASSTHROUGH_REASON
    # Same malformed payload on an approval-tier op still asks — the payload never mattered.
    asked = _review(_judge(ask_model=garbage), report=_report(4))
    assert asked.decision == "ask"


# --- FR-15/FR-16 the recommendation and its record ----------------------------------------------

def test_model_reasoning_is_recorded_verbatim_fr16():
    """The judge's reasoning *is* the audit justification (spec 011 FR-16, AC-19)."""
    reasoning = "Four pages are rewritten and one deleted; all recoverable from git."
    verdict = _review(_judge("approve", trust=True, reasoning=reasoning))
    assert verdict.reasoning == reasoning
    assert verdict.confidence == pytest.approx(0.8)


def test_ask_from_the_judge_is_attributed_to_the_judge_fr15():
    """An ask the model itself chose is not a filter downgrade (spec 011 FR-15)."""
    verdict = _review(_judge("ask", trust=True, reasoning="The delete is not entailed."))
    assert verdict.decision == "ask"
    assert verdict.source == "judge"
    assert verdict.reasoning == "The delete is not entailed."


def test_prompt_carries_objective_blast_radius_and_hint_fr15():
    """The judge sees what the operator would see (spec 011 FR-11/FR-15)."""
    captured: list[str] = []

    async def capturing(system, prompt):
        captured.append(system)
        captured.append(prompt)
        return json.dumps({"decision": "ask", "reasoning": "need the operator", "confidence": 0.1})

    _review(_judge(ask_model=capturing, trust=True), _report(score=4, executed=2))
    system, prompt = captured
    assert "You do not perform work" in system
    assert "install the weekly-digest skill" in prompt  # objective
    assert prompt.count("capability:ingest") == 2  # already executed, both of them
    assert "GATING OPERATION" in prompt
    assert "standing consent (trust mode) is ON" in prompt
    assert "recoverable from the workspace git repo" in prompt  # justification (FR-10)


def test_judge_satisfies_the_checker_contract_fr13():
    """Layer 2 may hold the judge through its abstract interface alone (spec 011 FR-13/FR-34)."""
    assert isinstance(_judge(), Checker)


# --- FR-22 the judge cannot execute -------------------------------------------------------------

def test_judge_module_imports_no_execution_module_fr22_ac11():
    """Structural proof that layer 3 cannot act (spec 011 FR-22, AC-11; FR-34)."""
    source = Path(judge.__file__).read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
            if node.level:  # `from . import x` / `from .x import y`
                imported.update(a.name for a in node.names)
    assert imported & FORBIDDEN_IMPORTS == set(), f"layer 3 must not import {imported & FORBIDDEN_IMPORTS}"


def test_judge_has_no_tools_and_writes_nothing_fr22(tmp_path, monkeypatch):
    """A whole review touches no file and offers no tool surface (spec 011 FR-22, AC-11)."""
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob("*"))
    verdict = _review(_judge("approve", trust=True))
    assert verdict.decision == "approve"
    assert set(tmp_path.rglob("*")) == before
    assert not [n for n in dir(judge.Judge) if "tool" in n.lower()]


def test_the_filter_is_pure_and_model_free_fr17():
    """The grant seam is callable with no model at all (spec 011 D4, FR-17)."""
    rec = judge.Recommendation(decision="approve", reasoning="reversible", confidence=1.0)
    kwargs = dict(experience_empty=False, max_score=4, ceiling=4, min_samples=3)
    assert judge.apply_filter(rec, trust=False, precedent=None, **kwargs).decision == "ask"
    assert judge.apply_filter(rec, trust=True, precedent=None, **kwargs).decision == "approve"
    assert judge.apply_filter(None, trust=True, precedent=None, **kwargs).decision == "ask"
