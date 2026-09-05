"""Layer 2 — workflow reporting: observe an execution, score it, accumulate it, pause it.

One **run** per user request (spec 011 FR-6), spanning the whole execution that request causes —
capability calls *and* the agent's native tool calls. Every operation layer 1 announces is scored
**1–5** and recorded with a one-line justification of its effect (FR-7/FR-10). At the first
operation whose score reaches the gate threshold the run **pauses** (FR-12) and hands the
accumulated report — the gating operation plus everything already executed (FR-11) — to a checker.

This layer **does not decide** (FR-13). It applies whatever verdict comes back. The default
checker returns ``ask``, so layer 2 is correct with layer 3 absent (AC-1).

Import direction (FR-34): imports ``execution_gate`` (the layer-1 contract) and ``config`` only.
It MUST NOT import ``judge``, ``experience`` or ``concierge``.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable

from . import config
from .execution_gate import ALLOW, Operation, Permit, strip_heredocs

# Operation lifecycle on a run record (FR-7).
STATUSES = ("pending", "executed", "declined", "not-reached")

# Verdict vocabulary (FR-15). `ask` is the safe default everywhere (FR-20/FR-21).
DECISIONS = ("approve", "decline", "ask")


@dataclass(frozen=True)
class ScoredOperation:
    """An announced operation plus layer 2's assessment of it (spec 011 FR-7)."""

    operation: Operation
    score: int  # 1-5
    modifiers: tuple[str, ...]  # names of the data-declared modifiers that fired
    justification: str  # one line: concrete effect + undo path (FR-10)
    status: str = "pending"

    def with_status(self, status: str) -> ScoredOperation:
        if status not in STATUSES:
            raise ValueError(f"unknown status {status!r}; expected one of {STATUSES}")
        return ScoredOperation(
            operation=self.operation,
            score=self.score,
            modifiers=self.modifiers,
            justification=self.justification,
            status=status,
        )

    def as_dict(self) -> dict:
        op = self.operation
        return {
            "op_id": op.op_id,
            "kind": op.kind,
            "name": op.name,
            "target": op.target,
            "tier": op.tier,
            "reversibility": op.reversibility,
            "external": op.external,
            "score": self.score,
            "modifiers": list(self.modifiers),
            "justification": self.justification,
            "status": self.status,
        }


@dataclass(frozen=True)
class RiskReport:
    """What the checker is given (spec 011 FR-11/FR-15).

    ``accumulated`` is the blast radius: the gating operation **and** every operation already
    executed in this run, so the operator is never shown a single opaque action.
    """

    run_id: str
    objective: str
    workspace: str
    gating: ScoredOperation
    accumulated: tuple[ScoredOperation, ...] = ()

    @property
    def max_score(self) -> int:
        return max((s.score for s in self.accumulated), default=self.gating.score)

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "objective": self.objective,
            "workspace": self.workspace,
            "gating": self.gating.as_dict(),
            "accumulated": [s.as_dict() for s in self.accumulated],
        }


@dataclass(frozen=True)
class Verdict:
    """The checker's answer (spec 011 FR-15).

    ``source`` records **which party decided** — required by Constitution P8 v2.0.0. It is
    ``judge`` for a model's own call, ``trust`` when standing consent carried it, ``precedent``
    when recorded experience did, ``filter`` when deterministic code downgraded the judge, and
    ``default`` when no checker was installed.
    """

    decision: str  # approve | decline | ask
    reasoning: str
    confidence: float = 0.0
    source: str = "judge"
    matched_precedent: str | None = None

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ValueError(f"unknown decision {self.decision!r}; expected one of {DECISIONS}")

    def as_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "source": self.source,
            "matched_precedent": self.matched_precedent,
        }


ASK_DEFAULT_REASON = "no checker is installed; asking is the safe default"


@runtime_checkable
class Checker(Protocol):
    """The single operation of the FR-13 contract."""

    async def review(self, report: RiskReport) -> Verdict: ...


class AskChecker:
    """Default checker — always asks (FR-13).

    Its existence is what makes layer 2 independently runnable and testable (FR-35), and it is the
    shape every failure path in layer 3 must collapse to (FR-20/FR-21).
    """

    async def review(self, report: RiskReport) -> Verdict:  # noqa: ARG002
        return Verdict(decision="ask", reasoning=ASK_DEFAULT_REASON, source="default")


# --- scoring modifiers: rules as data (spec 011 FR-8/FR-9, Constitution P12) -----------
#
# A modifier may describe ONLY the operation's own effect (FR-9). Trust mode, precedent, operator
# identity and the wording of the request are layer 3's inputs — a condition here receives an
# `Operation` and nothing else, which is what makes that constraint structural rather than a habit.
#
# The *weight* deliberately lives outside the declaration: it is read from
# `config.risk_weights()["modifiers"][name]` so an operator retunes scoring by hand-editing JSON,
# never by editing code (FR-32). The effect table (layer 1) is untouched by any of this — adding a
# modifier here requires no capability change, and vice versa (FR-36).


@dataclass(frozen=True)
class ScoringModifier:
    """One data-declared reason an operation scores above its tier's base (spec 011 FR-8)."""

    name: str
    description: str  # human-readable; shown to the operator verbatim in the justification (FR-10)
    condition: Callable[[Operation], bool]


# Phrases in a declared `reversibility` that mean git cannot put it back. Matched on meaning rather
# than one exact string, because the wording is owned by layer 1's effect table and varies
# ("no git revert covers it", "any run it enabled is not undone").
NO_GIT_UNDO_PHRASES: tuple[str, ...] = (
    "no git revert",
    "not undone",
    "irreversible",
    "cannot be undone",
    "no way to undo",
    "manually",
)

# Operations that hand the agent new executable behaviour. A privilege change is not undone by
# reverting the file that granted it, because whatever it enabled has already run.
PRIVILEGE_GRANTING_NAMES: frozenset[str] = frozenset({"import_skill"})

# …and the tool-level equivalent: a mutation landing in a workspace's `skills/` tree installs
# runnable instructions just as `import_skill` does, by a different door.
PRIVILEGE_GRANTING_TARGETS: tuple[str, ...] = ("skills/", ".claude/settings")

# Tool names whose target is a shell command rather than a path.
SHELL_TOOL_NAMES: tuple[str, ...] = ("Bash",)

# Coarse destructive-shell detection. `Bash` is not statically analysable and this does not pretend
# otherwise (011 Non-Goals, 010 D3): it over-fires rather than under-fires, and git remains the
# backstop. Requiring whitespace-or-end-of-command after the short verbs keeps quoted mentions
# (`grep -rn "rm" .`) from matching, while still catching a verb a wrapper leaves last
# (`find … | xargs rm`).
DESTRUCTIVE_SHELL_PATTERNS: tuple[str, ...] = (
    r"\brm(?=\s|$)",
    r"\brmdir\b",
    r"\bmv(?=\s|$)",
    r"\btruncate\b",
    r"\bdd(?=\s|$)",
    r"\bshred\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+push\s+(?:--force\b|-f\b)",
    r"\bgit\s+clean\s+-[a-z]*f",
    r"\bsed\s+-i\b",
    r"\bfind\b[^|]*\s-delete\b",
)

# A file-creating/truncating redirect, judged by **where it lands** rather than by its syntax
# (spec 011 FR-48). `>>` (append) and fd forms like `2>&1` are excluded: appending is the sanctioned
# way to touch the append-only ledger, and redirecting a stream is not a deletion.
_FILE_REDIRECT_RE = re.compile(r"(?<![0-9>&])>(?!>)")
_DESTRUCTIVE_SHELL_RE = re.compile("|".join(DESTRUCTIVE_SHELL_PATTERNS))

# Number of distinct path-like targets at which an operation counts as broad. Three, because one or
# two named files is the ordinary shape of focused work; a third suggests a sweep, and a sweep is
# what an operator wants to see before it happens.
BREADTH_TARGET_THRESHOLD = 3

_GLOB_RE = re.compile(r"[*?]|\[[^\]]+\]")
_PATH_LIKE_RE = re.compile(r"/|\.[A-Za-z0-9]{1,6}$")

# Targets whose corruption is not a normal revert: the ledger of what happened, the git database
# that would do the reverting, the operator's own trust settings, and the constitution.
SENSITIVE_TARGET_MARKERS: tuple[str, ...] = (
    ".git/",
    "vault/wiki/log.md",
    ".leader-settings.json",
    ".leader-experience.jsonl",
    ".leader-risk-weights.json",
    "memory/constitution.md",
)


def _normalized_target(operation: Operation) -> str:
    target = operation.target.replace("\\", "/").strip()
    if operation.name in SHELL_TOOL_NAMES:
        # FR-45: a here-document body is the data the command writes, not command syntax. Matching
        # effect patterns against it let a wiki page's own prose fire DESTRUCTIVE_SHELL and
        # EXTERNALLY_VISIBLE — a page describing `rm -rf` scored as one.
        target = strip_heredocs(target)
    return target


def _is_shell(operation: Operation) -> bool:
    return operation.name in SHELL_TOOL_NAMES


def _target_items(target: str) -> tuple[str, ...]:
    """Path-like tokens in a target, so a command's flags and words do not read as breadth."""
    tokens = (t.strip("\"'`,") for t in re.split(r"[\s,]+", target) if t)
    return tuple(t for t in tokens if t and _PATH_LIKE_RE.search(t))


# The one place the assistant writes in bulk by design: its own durable knowledge store (P1) and its
# generated artifacts. A write here is the job, not a sweep — see spec 011 FR-43 / D11.
KNOWLEDGE_STORE_MARKERS: tuple[str, ...] = ("vault/wiki/", "vault/output/")


def _confined_to_knowledge_store(operation: Operation) -> bool:
    """True when every path-like target is inside vault/wiki/ or vault/output/ and none is sensitive.

    Breadth exists to surface a sweep the operator did not ask for; a bulk ingest into the knowledge
    store is exactly the sweep they did ask for, so it must not gate on page count (FR-43). Narrower
    than zeroing the modifier: a single escaping path or a sensitive control file (e.g.
    vault/wiki/log.md) disqualifies the whole operation, keeping breadth armed everywhere else.
    """
    target = _normalized_target(operation)
    items = _target_items(target)
    if not items:
        return False
    if any(marker in item for item in items for marker in SENSITIVE_TARGET_MARKERS):
        return False
    return all(any(marker in item for marker in KNOWLEDGE_STORE_MARKERS) for item in items)


def _escapes_git(operation: Operation) -> bool:
    text = operation.reversibility.lower()
    return any(phrase in text for phrase in NO_GIT_UNDO_PHRASES)


def _grants_privilege(operation: Operation) -> bool:
    if operation.name in PRIVILEGE_GRANTING_NAMES:
        return True
    if operation.tier == "auto":
        # Reading a skill file grants nothing; installing or rewriting one does.
        return False
    target = _normalized_target(operation)
    return any(marker in target for marker in PRIVILEGE_GRANTING_TARGETS)


def _destructive_shell(operation: Operation) -> bool:
    # FR-45: match the *normalized* target, which strips heredoc bodies. Scanning the raw
    # target let the prose of a page being written fire this modifier.
    return _is_shell(operation) and bool(_DESTRUCTIVE_SHELL_RE.search(_normalized_target(operation)))


def _changes_something(operation: Operation) -> bool:
    """Does this operation alter state at all (spec 011 FR-40)?

    The guard the two blast-radius modifiers share. Both match the target *text*, which cannot tell
    reading a path from writing it — so without this, `tail vault/wiki/log.md` scores as if it were
    rewriting the ledger, and listing three directories scores as a sweep. Extent is only extent
    when there is a change to be extensive about.
    """
    return operation.tier != "auto"


def _many_targets(operation: Operation) -> bool:
    if not _changes_something(operation):
        return False
    if _confined_to_knowledge_store(operation):
        return False
    target = _normalized_target(operation)
    if _GLOB_RE.search(target):
        return True
    return len(_target_items(target)) >= BREADTH_TARGET_THRESHOLD


def _sensitive_target(operation: Operation) -> bool:
    if not _changes_something(operation):
        return False
    target = _normalized_target(operation)
    return any(marker in target for marker in SENSITIVE_TARGET_MARKERS)


def _redirect_escapes_repo(operation: Operation) -> bool:
    """A shell redirect whose write is **not** covered by a git revert (spec 011 FR-48).

    Replaces the bare `>` token in DESTRUCTIVE_SHELL, which described the *transport* rather than the
    effect (FR-9/P12) and put `cat > vault/wiki/page.md` at exactly the gate threshold — pricing the
    creation of one page identically to `rm -rf` of the concepts tree. Confinement is read off the
    FR-42 reversibility wording, the same signal layer 1 already computed, so no path resolution
    happens here.
    """
    if not _is_shell(operation) or not _changes_something(operation):
        return False
    return bool(_FILE_REDIRECT_RE.search(_normalized_target(operation))) and _escapes_git(operation)


MODIFIERS: tuple[ScoringModifier, ...] = (
    ScoringModifier(
        name="IRREVERSIBLE_OUTSIDE_GIT",
        description="no git revert puts this back",
        condition=_escapes_git,
    ),
    ScoringModifier(
        name="EXTERNALLY_VISIBLE",
        description="the effect leaves this machine",
        condition=lambda op: bool(op.external),
    ),
    ScoringModifier(
        name="PRIVILEGE_GRANTING",
        description="grants the agent new executable behaviour",
        condition=_grants_privilege,
    ),
    ScoringModifier(
        name="DESTRUCTIVE_SHELL",
        description="shell command contains destructive tokens",
        condition=_destructive_shell,
    ),
    ScoringModifier(
        name="REDIRECT_ESCAPES_REPO",
        description="writes via a redirect that no git revert here covers",
        condition=_redirect_escapes_repo,
    ),
    ScoringModifier(
        name="BREADTH_MANY_TARGETS",
        description=f"changes {BREADTH_TARGET_THRESHOLD} or more targets, or a glob of them",
        condition=_many_targets,
    ),
    ScoringModifier(
        name="SENSITIVE_TARGET",
        description="changes state whose corruption is not a normal revert",
        condition=_sensitive_target,
    ),
)

SCORE_MIN = 1
SCORE_MAX = 5


def fired_modifiers(operation: Operation) -> tuple[ScoringModifier, ...]:
    """The modifiers whose condition holds for ``operation`` (spec 011 FR-8)."""
    return tuple(m for m in MODIFIERS if m.condition(operation))


def _one_line(text: str) -> str:
    return " ".join(text.split())


def justify(operation: Operation, fired: tuple[ScoringModifier, ...]) -> str:
    """One line: the concrete effect, its undo path, then why it scored up (spec 011 FR-10).

    Read verbatim by the operator on the approval card, so it names the *thing* — never the score.
    """
    what = f"{operation.name} on {operation.target or '(no target)'}"
    undo = operation.reversibility.strip() or "no declared undo path"
    line = f"{what}; {undo}"
    if fired:
        line += " — " + "; ".join(m.description for m in fired)
    return _one_line(line)


def _score_declared_risk(operation: Operation, weights: dict) -> ScoredOperation:
    """Score an operation from its declared risk level, not tier + modifiers (spec 011 FR-37).

    The first user is skill import: a symlink is trivially reversible, so the FR-8 reversibility
    modifiers would pin every install at the ceiling and hide the real signal — how dangerous the
    *skill* is. When the operation carries a level, that level (mapped through the hand-editable
    `skill_risk_level` table) is the whole score. An unrecognised level falls back to `medium`.
    """
    level = operation.declared_risk.strip().lower()
    level_map = weights.get("skill_risk_level") or config.DEFAULT_RISK_WEIGHTS["skill_risk_level"]
    default_map = config.DEFAULT_RISK_WEIGHTS["skill_risk_level"]
    raw = level_map.get(level, default_map.get(level, default_map["medium"]))
    what = f"{operation.name} on {operation.target or '(no target)'}"
    undo = operation.reversibility.strip() or "no declared undo path"
    return ScoredOperation(
        operation=operation,
        score=max(SCORE_MIN, min(SCORE_MAX, int(raw))),
        modifiers=(f"SKILL_RISK_{level.upper()}",),
        justification=_one_line(f"{what}; {undo} — declared risk: {level}"),
    )


def score_operation(operation: Operation) -> ScoredOperation:
    """Score one announced operation: tier base + fired modifier weights, clamped 1–5 (FR-8).

    Weights are read fresh from the hand-editable JSON on every call (FR-32), so a retune takes
    effect on the next operation without a restart. An unknown tier or a modifier missing from the
    file contributes its default rather than raising: a typo in a hand-edited config must not be
    able to switch scoring off.

    An operation carrying a **declared risk level** (spec 011 FR-37) is scored from that level
    instead — see ``_score_declared_risk``.
    """
    weights = config.risk_weights()
    if operation.declared_risk:
        return _score_declared_risk(operation, weights)
    bases = weights.get("tier_base") or {}
    defaults = config.DEFAULT_RISK_WEIGHTS["tier_base"]
    base = bases.get(operation.tier, defaults.get(operation.tier, SCORE_MAX))
    modifier_weights = weights.get("modifiers") or {}
    default_modifier_weights = config.DEFAULT_RISK_WEIGHTS["modifiers"]

    fired = fired_modifiers(operation)
    total = int(base) + sum(
        int(modifier_weights.get(m.name, default_modifier_weights.get(m.name, 0))) for m in fired
    )
    return ScoredOperation(
        operation=operation,
        score=max(SCORE_MIN, min(SCORE_MAX, total)),
        modifiers=tuple(m.name for m in fired),
        justification=justify(operation, fired),
    )


# --- the run (spec 011 FR-6/FR-7/FR-11/FR-12/FR-14) -----------------------------------

# Run lifecycle. `awaiting` and `declined` are both *closed to execution*: FR-12 forbids anything
# running past a gate whose verdict is outstanding, and FR-27 makes a decline final for the run.
RUN_STATES = ("running", "awaiting", "declined")

_AWAITING_REASON = "run paused awaiting a decision on a higher-risk operation (spec 011 FR-12)"

# Operations a paused run MUST still permit (spec 011 FR-49). `request_approval` is the channel
# Constitution P8 v2.0.0 requires to stay open — "fail closed to asking" is unsatisfiable if the
# asking channel is itself refused.
PAUSE_EXEMPT_NAMES: frozenset[str] = frozenset({"request_approval"})
_RUN_DECLINED_REASON = "run ended when an earlier operation was declined (spec 011 FR-27)"
_OP_DECLINED_REASON = "declined for this run and not re-asked (spec 011 FR-27)"


def operation_key(operation: Operation) -> str:
    """Within-run identity of an operation: what it is and what it touches.

    Deliberately *not* the FR-31 audit fingerprint — that is the experience store's contract and
    layer 2 must not depend on layer 3 (FR-34). This key exists only so a retried operation is
    recognised as the same one, and a declined one is never re-asked in the run.
    """
    return f"{operation.kind}:{operation.name}:{operation.target}"


def shape_key(operation: Operation) -> str:
    """Target-independent identity of an operation: what it is, not what it touches (spec 011 FR-38).

    The unit of batch consent. `operation_key` gates each distinct target on its own; this collapses
    every same-capability call — `import_skill` on any skill — to one shape, so approving one skill
    install can authorise the rest of a bulk install for the run without a card per skill.
    """
    return f"{operation.kind}:{operation.name}"


class WorkflowRun:
    """One run per user request — scores, accumulates, pauses (spec 011 FR-6).

    Implements the layer-1 ``Gate`` protocol, so a caller installs it for the whole execution a
    request causes with ``execution_gate.use_gate(run)`` and every announcement — capability call
    and agent tool call alike — lands here.

    It does not decide (FR-13): at the gate it hands the accumulated report to a checker and applies
    whatever verdict comes back. With the default ``AskChecker`` that is always ``ask``, which is why
    layer 2 is correct and testable with layer 3 absent (FR-35).

    It also does not persist: ``as_dict()`` returns the audit record and the caller writes it
    (FR-14). Keeping storage out of here keeps the layer free of a filesystem dependency.
    """

    def __init__(
        self,
        objective: str,
        workspace: str,
        checker: Checker | None = None,
        threshold: int | None = None,
    ) -> None:
        self.run_id = uuid.uuid4().hex[:12]
        self.objective = objective
        self.workspace = workspace
        self._checker: Checker = checker or AskChecker()
        self._threshold_override = threshold
        self._operations: list[ScoredOperation] = []
        self._state = "running"
        self._report: RiskReport | None = None
        self._verdict: Verdict | None = None
        self._awaiting_key: str | None = None
        self._awaiting_shape: str | None = None
        # Keys the operator (or checker) has permanently refused, and keys cleared for exactly one
        # retry. Two sets rather than one flag because a run may gate on several distinct shapes.
        self._refused: set[str] = set()
        self._granted: set[str] = set()
        # Shapes (kind:name) the operator cleared for the whole run — "approve all similar" (FR-38).
        # Unlike `_granted`, a shape grant is *not* spent by the first match: it stands for the run.
        self._granted_shapes: set[str] = set()

    # --- read-only state the concierge needs ------------------------------------------

    @property
    def threshold(self) -> int:
        """Gate threshold, read fresh unless the caller pinned one (spec 011 FR-12/FR-32)."""
        if self._threshold_override is not None:
            return self._threshold_override
        return config.gate_threshold()

    @property
    def state(self) -> str:
        return self._state

    @property
    def awaiting(self) -> bool:
        return self._state == "awaiting"

    @property
    def awaiting_key(self) -> str | None:
        """Within-run identity of the paused operation, for the caller to persist (FR-26).

        An ask outlives the request that raised it: the operator answers in a *later* call, by
        which time this run object is gone. Handing the key out — and taking it back through
        ``pre_grant`` — is what lets a fresh run honour a decision made against its predecessor
        without this layer knowing anything about sessions, cards or storage.
        """
        return self._awaiting_key

    def pre_grant(self, key: str) -> None:
        """Seed a one-shot grant for ``key`` before execution starts (spec 011 FR-26).

        The complement of ``awaiting_key``. The grant is spent by the first announcement that
        matches, exactly as an in-run ``resume(approved=True)`` grant is, so an approval authorises
        one retry of one shape — never a standing exemption.
        """
        if key:
            self._granted.add(key)

    @property
    def awaiting_shape(self) -> str | None:
        """Shape of the paused operation, for the caller to persist as the batch-consent target (FR-38)."""
        return self._awaiting_shape

    def pre_grant_shape(self, shape: str) -> None:
        """Seed a standing shape grant before execution starts — "approve all similar" (spec 011 FR-38).

        Unlike ``pre_grant``, this is not spent by the first match: every same-shape operation the
        resumed run announces is let through, so a bulk install of many skills completes on one
        approval. Scoped to this run only; a new request builds a fresh run with no grants (D9).
        """
        if shape:
            self._granted_shapes.add(shape)

    @property
    def pending_report(self) -> RiskReport | None:
        """The report behind an outstanding ask — what the operator must be shown (FR-11/FR-25)."""
        return self._report

    @property
    def verdict(self) -> Verdict | None:
        return self._verdict

    @property
    def operations(self) -> tuple[ScoredOperation, ...]:
        """Every scored operation, in announcement order (FR-7)."""
        return tuple(self._operations)

    @property
    def executed(self) -> tuple[ScoredOperation, ...]:
        return tuple(s for s in self._operations if s.status == "executed")

    # --- the FR-3 gate contract -------------------------------------------------------

    async def permit(self, operation: Operation) -> Permit:
        """Score, record, and either allow or pause (spec 011 FR-7/FR-11/FR-12)."""
        scored = score_operation(operation)
        key = operation_key(operation)

        # FR-12/FR-27: once a verdict is outstanding or a decline has landed, nothing further runs.
        # These are recorded as `not-reached` and never re-consulted with the checker — asking again
        # about the tail of a paused run is exactly the "one opaque action at a time" this replaces.
        if key in self._refused:
            self._operations.append(scored.with_status("not-reached"))
            return Permit(allow=False, reason=_OP_DECLINED_REASON)
        if self._state != "running":
            # FR-49: fail closed to *asking*, not to silence. An `auto`-tier operation changes
            # nothing, so refusing it only stops the assistant explaining itself; and refusing
            # `request_approval` collapses FR-15's three outcomes into an undocumented fourth (hang).
            if self._state == "awaiting" and (
                operation.tier == "auto" or operation.name in PAUSE_EXEMPT_NAMES
            ):
                self._operations.append(scored.with_status("executed"))
                return ALLOW
            self._operations.append(scored.with_status("not-reached"))
            reason = _AWAITING_REASON if self._state == "awaiting" else _RUN_DECLINED_REASON
            return Permit(allow=False, reason=reason)

        # An approved retry of the paused operation: spend the grant, settle the pending record in
        # place rather than appending a duplicate, and let it through (FR-26).
        if key in self._granted:
            self._granted.discard(key)
            self._settle(key, scored, "executed")
            return ALLOW

        # A standing "approve all similar" grant covers every same-shape operation for the run and is
        # not spent — it is what turns a bulk of gating operations into one decision (FR-38). On a
        # resumed run these are freshly announced (no pending entry), so they append as executed.
        if shape_key(operation) in self._granted_shapes:
            self._operations.append(scored.with_status("executed"))
            return ALLOW

        if scored.score < self.threshold:
            self._operations.append(scored.with_status("executed"))
            return ALLOW

        pending = scored.with_status("pending")
        self._operations.append(pending)
        report = self._report_for(pending)
        verdict = await self._checker.review(report)
        self._verdict = verdict

        if verdict.decision == "approve":
            self._operations[-1] = pending.with_status("executed")
            self._report = None
            return ALLOW
        if verdict.decision == "decline":
            self._operations[-1] = pending.with_status("declined")
            self._refused.add(key)
            self._state = "declined"
            self._report = report
            return Permit(allow=False, reason=verdict.reasoning or _OP_DECLINED_REASON)

        self._state = "awaiting"
        self._report = report
        self._awaiting_key = key
        self._awaiting_shape = shape_key(operation)
        return Permit(allow=False, reason=verdict.reasoning or _AWAITING_REASON)

    # --- resumption -------------------------------------------------------------------

    def resume(self, approved: bool, reasoning: str = "", source: str = "user", scope: str = "one") -> Verdict:
        """Apply the operator's answer to the outstanding ask (spec 011 FR-26/FR-27/FR-38).

        ``approved`` clears the run for exactly one retry of the paused operation, so execution can
        complete it in the same turn without the gate firing a second time. ``scope="shape"`` widens
        an approval to every same-shape operation for the run — "approve all similar" (FR-38). A
        refusal is final for the run: the same operation is never re-asked (FR-27), and nothing after
        it runs; ``scope`` is ignored on a decline (D8 — a decline never generalises).
        """
        if self._state != "awaiting" or self._awaiting_key is None:
            raise ValueError("run is not awaiting a decision")

        key = self._awaiting_key
        shape = self._awaiting_shape
        self._awaiting_key = None
        self._awaiting_shape = None
        if approved:
            self._state = "running"
            self._granted.add(key)
            if scope == "shape" and shape:
                self._granted_shapes.add(shape)
            self._report = None
            verdict = Verdict(
                decision="approve",
                reasoning=reasoning or "operator approved the accumulated report",
                confidence=1.0,
                source=source,
            )
        else:
            self._state = "declined"
            self._refused.add(key)
            self._settle(key, None, "declined")
            verdict = Verdict(
                decision="decline",
                reasoning=reasoning or "operator declined the accumulated report",
                confidence=1.0,
                source=source,
            )
        self._verdict = verdict
        return verdict

    # --- audit ------------------------------------------------------------------------

    def as_dict(self) -> dict:
        """The persistable run record (spec 011 FR-14, AC-19).

        JSON-serialisable and complete on its own: the objective, every operation with the modifiers
        that produced its score and its one-line justification, and the verdict with who decided and
        why. Written by the caller, never by this layer.
        """
        return {
            "run_id": self.run_id,
            "objective": self.objective,
            "workspace": self.workspace,
            "state": self._state,
            "threshold": self.threshold,
            "operations": [s.as_dict() for s in self._operations],
            "verdict": self._verdict.as_dict() if self._verdict else None,
            "report": self._report.as_dict() if self._report else None,
        }

    # --- internals --------------------------------------------------------------------

    def _report_for(self, gating: ScoredOperation) -> RiskReport:
        """FR-11: the gating operation **plus** everything already executed, in run order."""
        accumulated = tuple(s for s in self._operations if s.status == "executed") + (gating,)
        return RiskReport(
            run_id=self.run_id,
            objective=self.objective,
            workspace=self.workspace,
            gating=gating,
            accumulated=accumulated,
        )

    def _settle(self, key: str, scored: ScoredOperation | None, status: str) -> None:
        """Move the recorded `pending` entry for ``key`` to ``status``, in place."""
        for i in range(len(self._operations) - 1, -1, -1):
            entry = self._operations[i]
            if entry.status == "pending" and operation_key(entry.operation) == key:
                self._operations[i] = (scored or entry).with_status(status)
                return
        if scored is not None:
            self._operations.append(scored.with_status(status))
