"""Layer 1 ⇄ layer 2 contract: announce an operation, receive a permit (spec 011 FR-3).

This module is the **only** thing the execution layer (capabilities + the agent's tools) knows
about gating. It holds no policy: no score, no trust mode, no precedent, no judge. Layer 1 calls
``announce()`` before it acts and honours the ``Permit`` it gets back (FR-2).

The default gate allows everything, so layer 1 runs correctly with layers 2 and 3 absent
(FR-3, AC-1). Layer 2 installs a real gate for the duration of a run via ``use_gate``.

``permit`` is **async** on purpose: the enforcement point for the agent's native tools is the SDK's
async ``PreToolUse`` hook (FR-4, D2), which is what makes a genuine pause possible.

Import direction (FR-34): this module imports neither ``workflow`` nor ``judge``. Anything richer
than ``Operation``/``Permit`` belongs on the far side of the contract.
"""

from __future__ import annotations

import re
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator, Protocol, runtime_checkable

# Effect tiers, restated here as plain strings so layer 1's declaration needs no import from
# layer 2. `capabilities.EFFECTS` remains the authority for which capability has which tier.
TIERS = ("auto", "reversible", "approval")


# --- shell effect vocabulary (spec 011 FR-39) -----------------------------------------
#
# Shared *description* of what a shell command does, not policy about it: no score, no threshold, no
# trust mode. It lives in the contract module because two layers need the same answer and neither may
# import the other (FR-34) — layer 1 to declare the tier, the experience store to fingerprint the
# command's effect class (FR-41).
#
# The list is **positive**: a command is read-only only if every program in it is recognised as such.
# An unknown program means "assume it mutates", so the failure direction is more asking, never less.
# This is recognition of known-safe programs, not static analysis of shell (011 Non-Goals).

READ_ONLY_SHELL_REVERSIBILITY = "read-only — nothing to undo"

# Programs whose effect is confined to reading and printing. Deliberately narrow: filesystem and text
# inspection only. Anything that can take another command as its argument is excluded below, and
# anything not listed is treated as mutating.
READ_ONLY_PROGRAMS: frozenset[str] = frozenset(
    {
        "awk", "basename", "cat", "cmp", "column", "cut", "diff", "dirname", "du", "echo", "file",
        "find", "fold", "git", "grep", "head", "jq", "ls", "nl", "printf", "pwd", "readlink",
        "realpath", "rg", "sed", "sort", "stat", "tail", "tr", "tree", "uniq", "wc", "yq",
    }
)

# Programs whose argument *is* another command, so their own name says nothing about the effect
# (`find . | xargs rm`). The effect is the payload's, so these are unwrapped before classifying.
COMMAND_WRAPPERS: frozenset[str] = frozenset(
    {"bash", "sh", "zsh", "eval", "exec", "nohup", "script", "sudo", "time", "timeout", "watch", "xargs"}
)

# Wrappers that pass their payload through unchanged, so judging the payload judges the command
# (FR-39 delegation). Shell interpreters are excluded: they re-parse their argument, so the quoted
# body escapes segment splitting and a read payload cannot be trusted to be the whole command.
# `sudo` is excluded because its risk is the privilege, not the payload's effect.
_TRANSPARENT_WRAPPERS: frozenset[str] = frozenset({"nice", "time", "timeout", "xargs"})

# Flags whose *next token* is the program to run, so the payload decides the effect
# (`find -exec wc -c {} \;` reads; `find -exec rm {} \;` does not).
_DELEGATING_FLAGS: frozenset[str] = frozenset({"-exec", "-execdir"})

# Flags that turn an otherwise read-only program into a writing one. Per-program, because the same
# flag differs in meaning: `sed -i` edits in place while `grep -i` only ignores case.
_MUTATING_FLAGS: dict[str, tuple[str, ...]] = {
    "awk": ("-i", "--in-place"),
    "find": ("-delete", "-ok", "-fprint", "-fprintf", "-fls"),
    "sed": ("-i", "--in-place"),
    "sort": ("-o", "--output"),
}

# `git` is read-only per subcommand, so it is listed above but resolved here. Omissions are
# deliberate: `branch`, `remote` and `config` all have mutating forms.
_READ_ONLY_GIT_SUBCOMMANDS: frozenset[str] = frozenset(
    {"blame", "cat-file", "count-objects", "describe", "diff", "log", "ls-files", "ls-tree",
     "rev-parse", "shortlog", "show", "status"}
)

_SEGMENT_SPLIT = re.compile(r"\|\||&&|[;|&\n]")
# Redirect fragments that move a stream rather than write a file, stripped before the file-redirect
# test so `2>&1` and `2>/dev/null` do not read as writes.
_STREAM_REDIRECT = re.compile(r"[0-9]*>&[0-9-]+|[0-9]*>\s*/dev/null")
_FILE_REDIRECT = re.compile(r"(?<![0-9>&])>")
# Command substitution hides an arbitrary command from segment splitting, so its presence alone
# disqualifies the command.
_SUBSTITUTION = re.compile(r"\$\(|`")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def path_tokens(command: str) -> tuple[str, ...]:
    """Tokens that name a filesystem location, for the FR-42 confinement check.

    Deliberately over-inclusive: a sed script (`s/a/b/`) is indistinguishable from a relative path
    here and is returned as one. That is the safe direction, because the caller requires *every*
    token to resolve inside the workspace — a spurious token can only cost a command its downgrade,
    never earn it one.
    """
    tokens: list[str] = []
    for segment in _segments(_STREAM_REDIRECT.sub("", command)):
        for raw in segment.split():
            token = raw.strip("'\"")
            if token.startswith("-") or token in ("{}", ";", "\\", "\\;", "+"):
                continue
            if "/" in token or token.startswith("~") or token.startswith("$"):
                tokens.append(token)
    return tuple(tokens)


def effectful_programs(command: str) -> tuple[str, ...]:
    """Programs from the segments that are **not** read-only, sorted and deduplicated (FR-41).

    The identity of a mutating command: `ls -la && rm x` and `rm x; ls` both yield `("rm",)`, because
    a read-only helper is not part of what the command does. Classified per segment rather than by
    filtering names against the allowlist, so a conditionally-read-only program is judged on how it
    was actually called — `git push` yields `git`, while `git log` yields nothing.
    """
    effectful: set[str] = set()
    for segment in _segments(command):
        if _segment_is_read_only(segment):
            continue
        effectful.update(_segment_programs(segment))
    return tuple(sorted(effectful))


def is_read_only_shell(command: str) -> bool:
    """Is every part of ``command`` recognised as reading only (spec 011 FR-39)?

    False for anything unrecognised, so the caller's fallback is the pessimistic declaration. A
    quoted ``>`` inside an awk program reads as a redirect and costs the command its `auto` tier —
    that over-firing is the intended direction.
    """
    if not (command or "").strip():
        return False
    stripped = _STREAM_REDIRECT.sub("", command)
    if _FILE_REDIRECT.search(stripped) or _SUBSTITUTION.search(stripped):
        return False
    segments = _segments(stripped)
    return bool(segments) and all(_segment_is_read_only(s) for s in segments)


def _segments(command: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in _SEGMENT_SPLIT.split(command or "") if s.strip())


def _segment_programs(segment: str) -> tuple[str, ...]:
    """Programs one segment invokes, outermost first: its own, plus every command it delegates to.

    Unwrapping matters for both callers: `xargs rm` names `rm` nowhere a first-token scan would find
    it, which would leave the segment fingerprinted — and scored — as if `xargs` were the effect. The
    same holds one level down, for the program a `-exec` hands the matches to.
    """
    all_tokens = [t for t in segment.split() if t]
    tokens = list(all_tokens)
    # Leading assignments are environment, and a leading flag means the split landed mid-command
    # (`find … -exec wc {} \; -delete` leaves `-delete` as its own segment) — neither names a program.
    while tokens and (_ASSIGNMENT.match(tokens[0]) or tokens[0].startswith("-")):
        tokens.pop(0)
    programs: list[str] = []
    while tokens:
        program = _program_name(tokens[0])
        if not program:
            break
        programs.append(program)
        if program not in COMMAND_WRAPPERS:
            break
        # A wrapper's own flags and numeric arguments (`timeout 30 find …`) are not the wrapped
        # command; the first token that is neither is.
        tokens = [t for t in tokens[1:] if not t.startswith("-") and not t.isdigit()]
    programs.extend(_delegated_programs(all_tokens))
    return tuple(programs)


def _program_name(token: str) -> str:
    return token.strip("'\"").rsplit("/", 1)[-1]


def _delegated_programs(tokens: list[str]) -> tuple[str, ...]:
    return tuple(
        _program_name(tokens[index + 1])
        for index, token in enumerate(tokens[:-1])
        if token in _DELEGATING_FLAGS and _program_name(tokens[index + 1])
    )


def _segment_is_read_only(segment: str) -> bool:
    programs = _segment_programs(segment)
    if not programs:
        return False
    # Delegation (FR-39): the payload decides, so the innermost program must read; anything it passed
    # through must be a transparent wrapper or a reading program that handed work on (`find -exec`).
    if programs[-1] not in READ_ONLY_PROGRAMS:
        return False
    if any(p not in _TRANSPARENT_WRAPPERS and p not in READ_ONLY_PROGRAMS for p in programs[:-1]):
        return False
    args = [t for t in segment.split() if t][1:]
    mutating = {flag for p in programs for flag in _MUTATING_FLAGS.get(p, ())}
    if any(arg.split("=", 1)[0] in mutating for arg in args):
        return False
    if "git" in programs:
        subcommand = next((a for a in args if not a.startswith("-")), "")
        return subcommand in _READ_ONLY_GIT_SUBCOMMANDS
    return True


@dataclass(frozen=True)
class Operation:
    """One operation layer 1 is about to attempt (spec 011 FR-5).

    Carries enough for layer 2 to score it and layer 3 to judge it **without** calling back into
    layer 1: what it is, what it touches, its declared tier, how it is undone, and whether its
    effect leaves this machine.
    """

    kind: str  # "capability" | "tool"
    name: str  # capability name (e.g. "import_skill") or tool name (e.g. "Write")
    target: str  # resolved target: a path, workspace name, skill name, or command
    tier: str  # auto | reversible | approval
    reversibility: str  # human-readable undo path, or a statement that there is none
    external: bool = False  # does the effect leave this machine?
    # Danger of the thing being installed/run, distinct from how reversible the act is (spec 011
    # FR-37). Empty for ordinary operations; a level name (low|medium|high|critical) for a skill
    # import, where it is the skill's own declared `risk-level`. When set, layer 2 scores from it.
    declared_risk: str = ""
    detail: str = ""  # optional extra context for the audit record
    op_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"unknown effect tier {self.tier!r}; expected one of {TIERS}")


@dataclass(frozen=True)
class Permit:
    """Layer 2's answer to an announcement: act, or do not act and say why."""

    allow: bool
    reason: str | None = None


ALLOW = Permit(allow=True)


@runtime_checkable
class Gate(Protocol):
    """The single operation of the FR-3 contract."""

    async def permit(self, operation: Operation) -> Permit: ...


class AllowAllGate:
    """Default gate — permits everything (FR-3).

    Its existence is what makes layer 1 independently runnable and testable (FR-35): with no run
    installed, execution behaves exactly as it did before this feature.
    """

    async def permit(self, operation: Operation) -> Permit:  # noqa: ARG002
        return ALLOW


_DEFAULT_GATE = AllowAllGate()

# Per-task gate. A ContextVar rather than a module global so concurrent chat turns (each its own
# asyncio task) cannot see each other's run — the gate is scoped to the execution it governs.
_active_gate: ContextVar[Gate] = ContextVar("leader_active_gate", default=_DEFAULT_GATE)


@contextmanager
def use_gate(gate: Gate) -> Iterator[Gate]:
    """Install ``gate`` for the enclosing execution, restoring the previous one on exit."""
    token = _active_gate.set(gate)
    try:
        yield gate
    finally:
        _active_gate.reset(token)


def active_gate() -> Gate:
    return _active_gate.get()


async def announce(operation: Operation) -> Permit:
    """Announce an operation about to be attempted and return its permit (FR-2/FR-3).

    Layer 1 MUST call this before acting and MUST honour a denial. Never raises on the gate's
    behalf: a gate that itself fails is treated as a denial, because failing open would make the
    pause of FR-12 unenforceable.
    """
    gate = _active_gate.get()
    try:
        return await gate.permit(operation)
    except Exception as e:  # noqa: BLE001 — a broken gate must not become an open gate
        return Permit(allow=False, reason=f"gate error, refusing to proceed: {e}")


def deny_message(operation: Operation, permit: Permit) -> str:
    """Uniform text for a refused operation, used by the hook and by capability errors."""
    reason = permit.reason or "not permitted"
    return f"{operation.name} on {operation.target or '(no target)'} was not permitted: {reason}"
