"""Past experience — the append-only decision store behind precedent (spec 011 FR-28…FR-33).

This is the memory that lets the checker ask **less** over time without ever silently broadening
consent. Four jobs, and nothing else:

1. **Fingerprints** (FR-31) — a deterministic, readable canonical string for an operation and for
   an objective, so a precedent match is explainable to the operator ("you approved this same
   shape 4 times") *without* running the judge. Exact strings only: no embeddings, no fuzzy
   similarity, no vector store (D5, Constitution P1/P10).
2. **Recording** (FR-29/FR-30) — one JSON object per line appended to
   ``config.experience_path()`` after **every** decision, off the response path and never able to
   fail it.
3. **Precedent lookup** (FR-17 support) — counts of what the **operator** decided about one
   fingerprint inside the configured window.
4. **Suggest-only analysis** (FR-32, AC-18, D7) — computes ``suggested_*`` values from the
   accumulated records and applies **nothing**. A human edits
   ``config.risk_weights_path()``; this module never writes it.

Adapted from the ``transcribe-voice-memo`` reference pattern, keeping its two load-bearing
properties: ``analyze()`` suggests but never applies (D7), and a cold start says "no records"
rather than guessing (FR-20).

Import direction (FR-34): ``config`` plus the layer-1 ``Operation`` type and stdlib. This module
holds no policy — it neither scores nor decides, and it MUST NOT import ``capabilities``,
``judge`` or ``concierge``.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config
from .execution_gate import Operation, effectful_programs, is_read_only_shell

log = logging.getLogger(__name__)

# The record shape is versioned because the file is append-only: records written today must stay
# readable by every later build, so the shape can only ever be added to, never reinterpreted.
SCHEMA_VERSION = 1

# Decision vocabulary, mirroring `workflow.DECISIONS` as plain data rather than an import — this
# module is downstream of nothing and validates nothing on the write path (see `record`).
DECISIONS = ("approve", "decline", "ask")

# Who decided (FR-29). Constitution P8 v2.0.0 requires every record to name the deciding party.
SOURCES = ("user", "judge", "trust", "precedent")

# The **only** source that can create precedent (FR-17). See `lookup`.
OPERATOR_SOURCE = "user"

# Coarse label for a 1-5 score (FR-29). Data, so the vocabulary shown in an audit record can be
# reworded without touching the scoring model in layer 2 (FR-36).
SCORE_BANDS: dict[int, str] = {
    1: "routine",
    2: "reversible",
    3: "notable",
    4: "consequential",
    5: "critical",
}


def band(score: int) -> str:
    """Band label for a score, clamped into 1-5 so a miscomputed score still records something."""
    try:
        clamped = max(1, min(5, int(score)))
    except (TypeError, ValueError):
        clamped = 1
    return SCORE_BANDS[clamped]


# --- fingerprints (spec 011 FR-31) ----------------------------------------------------------
#
# Normalisation rules, in one place because they define what "the same shape" means and therefore
# what consent granted once will cover next time:
#
#   * `kind` and `name` keep their identifier casing (`Write` stays `Write`) — they are the part an
#     operator reads to recognise the operation, and the SDK's tool names are case-sensitive.
#   * the target is lowercased; every target we see is a path, a skill name, a workspace name or a
#     shell command, none of which distinguishes shapes by case alone.
#   * paths are made workspace-relative at the first `vault`/`sessions`/`skills` anchor, so the same
#     operation in two workspaces (and on two machines) fingerprints identically — experience is
#     global (FR-33).
#   * a **filename** leaf is collapsed to `*`: writing `concepts/widgets.md` and
#     `concepts/gadgets.md` is one shape. A directory leaf is kept, because the directory *is* the
#     target.
#   * volatile tokens — uuids, hex blobs, timestamps, long digit runs — collapse to `{id}`/`{ts}`/
#     `{n}`, otherwise every occurrence would be a brand-new shape and precedent could never form.
#   * `Bash` reduces to an **effect class** — `read-only`, or the sorted set of its effect-bearing
#     programs (FR-41). Arguments are not statically analysable (Non-Goals) and the earlier rule (the
#     first three program names, in order) made every phrasing of one intent a new shape, so
#     precedent could never reach FR-17's sample count. Coarsening is one-way and `Bash`-only.
#
# `op_id` is deliberately absent: it identifies an occurrence, not a shape.

_PATH_ANCHORS = ("vault", "sessions", "skills")

_UUID = re.compile(r"[0-9a-f]{8}-?(?:[0-9a-f]{4}-?){3}[0-9a-f]{12}", re.IGNORECASE)
_HEXBLOB = re.compile(r"\b[0-9a-f]{12,}\b", re.IGNORECASE)
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}(?:[t_ ]\d{2}[:-]?\d{2}(?:[:-]?\d{2})?)?", re.IGNORECASE)
_LONG_DIGITS = re.compile(r"\d{3,}")

# Effect classes a shell command collapses to (FR-41). Named rather than derived so they read as
# categories on an audit record: `tool:Bash:read-only` is a sentence an operator can check.
READ_ONLY_COMMAND_CLASS = "read-only"
WRITE_COMMAND_CLASS = "write"
_COMMAND_CLASS_PROGRAM_LIMIT = 3


def _collapse_volatile(text: str) -> str:
    """Replace per-occurrence tokens with placeholders (order matters: broadest pattern last)."""
    text = _UUID.sub("{id}", text)
    text = _TIMESTAMP.sub("{ts}", text)
    text = _HEXBLOB.sub("{id}", text)
    return _LONG_DIGITS.sub("{n}", text)


def _normalise_command(target: str) -> str:
    """A shell command reduced to its **effect class** (spec 011 FR-41).

    ``rm -rf x && git status`` and ``ls; rm x`` both -> ``rm``; any recognised read-only command ->
    ``read-only``. Order, arguments and read-only helpers are dropped, so slight variations of one
    intent canonicalise to one string and precedent can actually accumulate — matching itself stays
    exact equality on this form, with no similarity scoring anywhere (D5).
    """
    if is_read_only_shell(target):
        return READ_ONLY_COMMAND_CLASS
    effectful = effectful_programs(target)
    if not effectful:
        # Built only from read programs, yet not read-only: a redirect, a substitution or an
        # in-place flag is doing the writing, and no program name names it.
        return WRITE_COMMAND_CLASS
    return "+".join(effectful[:_COMMAND_CLASS_PROGRAM_LIMIT])


def _normalise_path(target: str) -> str:
    """Workspace-relative, leaf-collapsed path (see the rules above)."""
    parts = [p for p in target.replace("\\", "/").split("/") if p not in ("", ".")]
    anchor = next(
        (i for i in range(len(parts) - 1, -1, -1) if parts[i] in _PATH_ANCHORS),
        None,
    )
    if anchor is not None:
        parts = parts[anchor:]
    elif len(parts) > 2:
        # No anchor: keep the last two segments so the shape stays recognisable without leaking a
        # machine-specific prefix that would make the same operation look new on another host.
        parts = ["..."] + parts[-2:]
    if not parts:
        return "-"
    leaf = parts[-1]
    if "." in leaf.lstrip(".") and len(parts) > 1:
        parts[-1] = "*"
    return "/".join(_collapse_volatile(p) for p in parts)


def _normalise_target(kind: str, name: str, target: str) -> str:
    target = (target or "").strip().lower()
    if not target:
        return "-"
    if kind == "tool" and name.strip().lower() == "bash":
        return _normalise_command(target)
    if "/" in target or "\\" in target:
        return _normalise_path(target)
    return _collapse_volatile(target)


def operation_fingerprint(operation: Operation) -> str:
    """Canonical, human-auditable identity of an operation's **shape** (spec 011 FR-31).

    Examples: ``capability:import_skill:second-brain-ingest`` ·
    ``tool:Write:vault/wiki/concepts/*`` · ``tool:Bash:read-only`` · ``tool:Bash:rm``.

    Stable across runs, workspaces and machines, and readable enough to put in front of an
    operator — which is the whole point: a precedent that cannot be explained cannot be audited
    (D5). Excludes ``op_id``, which is per-occurrence.
    """
    kind = (operation.kind or "?").strip().lower()
    name = (operation.name or "?").strip() or "?"
    return f"{kind}:{name}:{_normalise_target(kind, name, operation.target)}"


_WORD = re.compile(r"[a-z0-9]+")

# Deliberately tiny: an aggressive stopword list would make unrelated requests collide, and a
# collision here is a *wrongly* claimed precedent.
_STOPWORDS = frozenset(
    """a an and are as at be by can could did do does for from get got had has have how
    i if in into is it its just let make me my of on or our please put should so than that
    the their then there these this to too us was we were what when where which will with
    would you your""".split()
)

_OBJECTIVE_TOKEN_LIMIT = 8


def objective_fingerprint(objective: str) -> str:
    """Stable token signature of a free-text request (spec 011 FR-31).

    **Honest limitation:** an objective is prose and has no canonical form. This normalises to
    sorted, deduplicated, stopword-stripped tokens (capped at eight) so the *same* request worded
    the same way fingerprints identically — but two phrasings of one intent will differ, and two
    unrelated requests sharing vocabulary may collide. It is therefore recorded as **context on a
    decision**, never as the key that unlocks one: precedent is keyed on the operation fingerprint
    alone (D5), which is exact.
    """
    tokens = sorted(
        {
            t
            for t in _WORD.findall((objective or "").lower())
            if len(t) >= 3 and t not in _STOPWORDS
        }
    )[:_OBJECTIVE_TOKEN_LIMIT]
    return "obj:" + ("-".join(tokens) if tokens else "-")


def precedent_id(fingerprint: str) -> str:
    """Stable id for the precedent a fingerprint accumulates, quotable in a record and a reply."""
    return f"prec:{fingerprint}"


# --- recording (spec 011 FR-29/FR-30) -------------------------------------------------------

# In-process serialisation of appends. Writes may arrive from several executor threads at once;
# the lock keeps whole lines whole. It never guards a read, so a reader is never blocked.
_write_lock = threading.Lock()

# Strong references to in-flight writes. A fire-and-forget future with no owner can be garbage
# collected mid-flight, which would silently drop records (FR-30).
_pending: set = set()


def _build_record(
    *,
    run_id: str,
    operation: Operation | str,
    decision: str,
    source: str,
    score: int,
    objective: str,
    workspace: str,
    outcome: str,
    matched_precedent: str | None,
    reasoning: str,
) -> dict:
    """The FR-29 record. Validates nothing: a malformed decision must still leave a trace."""
    fingerprint = (
        operation if isinstance(operation, str) else operation_fingerprint(operation)
    )
    return {
        "schema": SCHEMA_VERSION,
        "record_id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "workspace": workspace,
        "objective_fingerprint": objective_fingerprint(objective),
        "operation_fingerprint": fingerprint,
        "score": score,
        "band": band(score),
        "decision": decision,
        "source": source,
        "matched_precedent": matched_precedent,
        "outcome": outcome,
        "reasoning": reasoning,
    }


def record(
    *,
    run_id: str,
    operation: Operation | str,
    decision: str,
    source: str,
    score: int = 1,
    objective: str = "",
    workspace: str = "",
    outcome: str = "",
    matched_precedent: str | None = None,
    reasoning: str = "",
    path: Path | None = None,
) -> bool:
    """Append exactly one decision record (spec 011 FR-29). Returns whether it landed.

    **Append-only**: opened in ``"a"`` mode, one ``json.dumps`` + newline, existing lines never
    read, rewritten or truncated. **Never raises** (FR-30): a full disk, a read-only path or an
    unserialisable field is logged and swallowed, because losing a precedent is survivable and
    failing the operator's turn is not.

    Prefer ``record_async`` from a request path; this is the blocking form it delegates to.
    """
    try:
        target = path or config.experience_path()
        line = json.dumps(
            _build_record(
                run_id=run_id,
                operation=operation,
                decision=decision,
                source=source,
                score=score,
                objective=objective,
                workspace=workspace,
                outcome=outcome,
                matched_precedent=matched_precedent,
                reasoning=reasoning,
            ),
            sort_keys=True,
        )
        with _write_lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return True
    except Exception as e:  # noqa: BLE001 — FR-30/AC-16: experience must never break a response
        log.warning("experience record dropped: %s", e)
        return False


def _forget(fut) -> None:
    _pending.discard(fut)
    try:
        fut.result()
    except Exception as e:  # noqa: BLE001 — the executor cannot re-raise into the response
        log.warning("experience record dropped: %s", e)


def record_async(**kwargs):
    """Schedule a record off the response path (spec 011 FR-30, AC-16). Fire and forget.

    Call it; do not await it. It hands the blocking append to the default executor so no file I/O
    happens on the event loop, keeps a strong reference to the future so it cannot be collected
    mid-flight, and swallows every failure. With no running loop it falls back to the synchronous
    ``record`` — which is equally safe, since that never raises either.

    The returned future exists so a test can await the write deterministically (see ``drain``);
    production callers should ignore it. ``None`` means the write already happened inline.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        record(**kwargs)
        return None
    try:
        fut = loop.run_in_executor(None, functools.partial(record, **kwargs))
    except Exception as e:  # noqa: BLE001 — a loop shutting down must not break the turn
        log.warning("experience record not scheduled: %s", e)
        return None
    _pending.add(fut)
    fut.add_done_callback(_forget)
    return fut


def pending_count() -> int:
    """How many writes are in flight. Diagnostics and tests only."""
    return len(_pending)


async def drain() -> None:
    """Await every in-flight write. For tests and shutdown; never on the response path."""
    while _pending:
        await asyncio.gather(*tuple(_pending), return_exceptions=True)


# --- reading (spec 011 FR-17 support, FR-20) ------------------------------------------------


def load(path: Path | None = None) -> list[dict]:
    """Every readable record, oldest line first.

    The file is hand-inspectable and therefore hand-corruptible: a malformed line, a non-object
    line and a truncated final line are **skipped**, not fatal. Unknown fields are preserved and
    ignored, which is what lets a newer build's records be read by an older one.
    """
    target = path or config.experience_path()
    try:
        text = target.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, OSError):
        return []
    records: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            log.debug("skipping malformed experience line")
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
    return records


def is_empty(path: Path | None = None) -> bool:
    """True when there is nothing to learn from — the FR-20 cold-start check (AC-9).

    True for a missing file, an empty file, and a file whose every line is unreadable.
    """
    return not load(path)


def _parsed_timestamp(record_: dict) -> datetime | None:
    raw = record_.get("timestamp")
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class PrecedentSummary:
    """What the operator has already decided about one operation shape (spec 011 FR-17).

    The five leading fields are the contract layer 3 maps onto; the rest is audit colour.
    """

    precedent_id: str
    fingerprint: str
    approvals: int
    declines: int
    last_decision: str
    last_decided_at: str = ""
    window_days: int = 0
    contributing: tuple[str, ...] = ()

    @property
    def samples(self) -> int:
        return self.approvals + self.declines

    def as_dict(self) -> dict:
        return {
            "precedent_id": self.precedent_id,
            "fingerprint": self.fingerprint,
            "approvals": self.approvals,
            "declines": self.declines,
            "last_decision": self.last_decision,
            "last_decided_at": self.last_decided_at,
            "window_days": self.window_days,
        }


def lookup(fingerprint: str, path: Path | None = None) -> PrecedentSummary | None:
    """Operator precedent for one operation shape, or ``None`` if there is none (spec 011 FR-17).

    **Only ``source == "user"`` records count.** This is the single most important rule in this
    module. A judge's own auto-approval must never become the precedent that justifies the next
    auto-approval — that is consent bootstrapping itself out of nothing, and it would turn one
    lucky grant into standing authority. ``trust`` and ``precedent`` sources are excluded for the
    same reason: neither is a fresh human decision.

    Records outside ``config.precedent_window_days()`` are excluded, as are records whose
    timestamp will not parse — unverifiable window membership can justify neither a skip (FR-17)
    nor a refusal (FR-19).

    Applies **no** threshold: the minimum sample count and the ceiling are layer 3's filter to
    apply (FR-17/FR-18). This function only reports what happened.
    """
    window_days = config.precedent_window_days()
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    approvals = 0
    declines = 0
    latest: tuple[datetime, str, str] | None = None
    contributing: list[str] = []

    for record_ in load(path):
        if record_.get("operation_fingerprint") != fingerprint:
            continue
        if record_.get("source") != OPERATOR_SOURCE:
            continue
        when = _parsed_timestamp(record_)
        if when is None or when < cutoff:
            continue
        decision = record_.get("decision")
        if decision == "approve":
            approvals += 1
        elif decision == "decline":
            declines += 1
        else:
            continue
        rid = record_.get("record_id")
        if isinstance(rid, str):
            contributing.append(rid)
        if latest is None or when >= latest[0]:
            latest = (when, decision, when.isoformat())

    if latest is None:
        return None
    return PrecedentSummary(
        precedent_id=precedent_id(fingerprint),
        fingerprint=fingerprint,
        approvals=approvals,
        declines=declines,
        last_decision=latest[1],
        last_decided_at=latest[2],
        window_days=window_days,
        contributing=tuple(contributing),
    )


# --- suggest-only analysis (spec 011 FR-32, AC-18, D7) --------------------------------------

NO_RECORDS = "No experience records available"

_ANALYSIS_NOTE = (
    "Suggestions only — nothing was applied. Edit the thresholds by hand in "
    "the risk-weights file if you agree with them (spec 011 FR-32, D7)."
)


def _clamp_score(value: int) -> int:
    return max(1, min(5, value))


def analyze(path: Path | None = None) -> dict:
    """Calibration view over the accumulated records — **suggests, never applies** (FR-32, D7).

    Reports per-fingerprint approval rates, the shapes the operator has approved consistently
    enough to be candidates for less friction, and the shapes they have ever declined. Then
    derives ``suggested_gate`` and ``suggested_precedent_free_ceiling`` the way the
    ``transcribe-voice-memo`` reference derives ``suggested_safe`` / ``suggested_warn``: from the
    boundary between what the operator accepted and what they refused.

    **Writes nothing.** Not the weights file, not the experience file, not anywhere. Self-tuning
    thresholds would let the system quietly widen its own consent (D7), so applying a suggestion
    is a human act. Reads the full history rather than the precedent window, because calibration
    wants all the evidence there is.

    A cold start returns ``{"error": NO_RECORDS}`` rather than a guess (FR-20).
    """
    records = load(path)
    if not records:
        return {"error": NO_RECORDS, "total_records": 0, "note": _ANALYSIS_NOTE}

    shapes: dict[str, dict] = {}
    approved_scores: list[int] = []
    declined_scores: list[int] = []

    for record_ in records:
        fingerprint = record_.get("operation_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            continue
        stats = shapes.setdefault(
            fingerprint,
            {
                "fingerprint": fingerprint,
                "precedent_id": precedent_id(fingerprint),
                "records": 0,
                "operator_approvals": 0,
                "operator_declines": 0,
                "judge_approvals": 0,
                "asks": 0,
                "max_score": 0,
            },
        )
        stats["records"] += 1
        score = record_.get("score")
        score = score if isinstance(score, int) else 0
        stats["max_score"] = max(stats["max_score"], score)

        decision = record_.get("decision")
        operator = record_.get("source") == OPERATOR_SOURCE
        if decision == "approve":
            if operator:
                stats["operator_approvals"] += 1
                approved_scores.append(_clamp_score(score or 1))
            else:
                stats["judge_approvals"] += 1
        elif decision == "decline":
            if operator:
                stats["operator_declines"] += 1
                declined_scores.append(_clamp_score(score or 1))
        elif decision == "ask":
            stats["asks"] += 1

    for stats in shapes.values():
        operator_decisions = stats["operator_approvals"] + stats["operator_declines"]
        stats["operator_decisions"] = operator_decisions
        stats["approval_rate"] = (
            round(stats["operator_approvals"] / operator_decisions, 3)
            if operator_decisions
            else None
        )

    min_samples = config.precedent_min_samples()
    result: dict = {
        "total_records": len(records),
        "distinct_shapes": len(shapes),
        "precedent_min_samples": min_samples,
        "shapes": sorted(shapes.values(), key=lambda s: -s["records"]),
        # Approved consistently enough that precedent could carry them: candidates for a lower
        # threshold. Any operator decline disqualifies a shape outright (D8).
        "suggested_trusted_shapes": sorted(
            s["fingerprint"]
            for s in shapes.values()
            if s["operator_approvals"] >= min_samples and s["operator_declines"] == 0
        ),
        # Ever refused: these must keep asking whatever else changes.
        "suggested_always_ask_shapes": sorted(
            s["fingerprint"] for s in shapes.values() if s["operator_declines"] > 0
        ),
        "note": _ANALYSIS_NOTE,
    }

    if approved_scores and declined_scores:
        highest_approved = max(approved_scores)
        lowest_declined = min(declined_scores)
        result["max_approved_score"] = highest_approved
        result["min_declined_score"] = lowest_declined
        result["suggested_gate"] = _clamp_score(lowest_declined)
        result["suggested_precedent_free_ceiling"] = _clamp_score(
            highest_approved if highest_approved < lowest_declined else lowest_declined - 1
        )
    elif approved_scores:
        highest_approved = max(approved_scores)
        result["max_approved_score"] = highest_approved
        # Never refused anything yet, so the only defensible boundary is just above what has been
        # waved through — and it stays a suggestion.
        result["suggested_gate"] = _clamp_score(highest_approved + 1)
        result["suggested_precedent_free_ceiling"] = _clamp_score(highest_approved)
    elif declined_scores:
        lowest_declined = min(declined_scores)
        result["min_declined_score"] = lowest_declined
        result["suggested_gate"] = _clamp_score(lowest_declined)
        result["suggested_precedent_free_ceiling"] = _clamp_score(lowest_declined - 1)

    return result
