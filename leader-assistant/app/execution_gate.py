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

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator, Protocol, runtime_checkable

# Effect tiers, restated here as plain strings so layer 1's declaration needs no import from
# layer 2. `capabilities.EFFECTS` remains the authority for which capability has which tier.
TIERS = ("auto", "reversible", "approval")


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
