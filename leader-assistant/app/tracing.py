"""Langfuse tracing over the app's `claude_agent_sdk.query()` call sites (spec 013 FR-1..FR-6).

Optional and fail-safe: ``get_client()`` reads ``LANGFUSE_PUBLIC_KEY``/``LANGFUSE_SECRET_KEY``/
``LANGFUSE_BASE_URL`` straight from the environment and returns a disabled no-op client when the
keys are absent — true for the whole test suite, since ``tests/conftest.py::no_real_dotenv`` keeps
it off the real ``.env`` (spec 03-workspace §0). Every helper below is therefore inert (no network,
no exception) unless an operator has configured Langfuse, so it needs no feature flag of its own.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from langfuse import get_client, propagate_attributes


def _meta(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


@contextmanager
def generation(
    name: str,
    *,
    model: str,
    input: Any = None,  # noqa: A002 — matches Langfuse's own kwarg name
    session_id: str | None = None,
    trace_name: str | None = None,
    **metadata: Any,
) -> Iterator[Any]:
    """One traced model call — a Langfuse generation, nested under whatever span/generation (if
    any) is already open in this asyncio task (spec 013 FR-2).

    ``session_id`` (typically a conversation id) groups every generation belonging to the same
    conversation into one Langfuse session (spec 013 FR-4).
    """
    meta = _meta(**metadata)
    with propagate_attributes(session_id=session_id, metadata=meta, trace_name=trace_name):
        with get_client().start_as_current_observation(
            name=name, as_type="generation", model=model, input=input, metadata=meta
        ) as gen:
            yield gen


@contextmanager
def span(
    name: str,
    *,
    session_id: str | None = None,
    trace_name: str | None = None,
    **metadata: Any,
) -> Iterator[Any]:
    """A parent observation for grouping child generations (e.g. ingest's two phases, FR-5)."""
    meta = _meta(**metadata)
    with propagate_attributes(session_id=session_id, metadata=meta, trace_name=trace_name):
        with get_client().start_as_current_observation(
            name=name, as_type="span", metadata=meta
        ) as s:
            yield s


def usage_and_cost(
    usage: dict[str, Any] | None, total_cost_usd: float | None
) -> tuple[dict[str, int] | None, dict[str, float] | None]:
    """Map a ``claude_agent_sdk.ResultMessage``'s usage/cost onto Langfuse's generation fields."""
    usage_details = {k: v for k, v in (usage or {}).items() if isinstance(v, int)} or None
    cost_details = {"total": total_cost_usd} if total_cost_usd is not None else None
    return usage_details, cost_details


def flush() -> None:
    """Force-send buffered spans (spec 013 FR-6) — best-effort, never raises."""
    try:
        get_client().flush()
    except Exception:  # noqa: BLE001 — telemetry teardown must never break shutdown
        pass
