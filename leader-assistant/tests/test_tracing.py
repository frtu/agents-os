"""Langfuse tracing fail-safe + pure mapping (spec 013-langfuse-observability FR-6/FR-4).

`no_real_dotenv` (conftest) already keeps every test off the real `.env`, so
`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are unset here by default — these tests make that
fail-safe property explicit rather than merely relying on it as a side effect.
"""

from __future__ import annotations

from app import tracing


def test_generation_is_noop_without_credentials(monkeypatch):  # spec 013 FR-6 / test_..._fr6
    """Entering/exiting/updating a generation must not raise or reach the network when unconfigured."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    with tracing.generation("chat-turn", model="sonnet", input="hi", session_id="conv-1") as gen:
        gen.update(output="hello", usage_details={"input": 3}, cost_details={"total": 0.0})

    tracing.flush()  # spec 013 FR-7: must also be a safe no-op


def test_span_nests_generations_without_credentials(monkeypatch):  # spec 013 FR-2/FR-6
    """The ingest span/generation nesting used in production must not raise when unconfigured."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    with tracing.span("ingest", workspace="demo"):
        with tracing.generation("ingest-phase1", model="sonnet", input="a") as g1:
            g1.update(output="unstructured")
        with tracing.generation("ingest-phase2", model="sonnet", input="b") as g2:
            g2.update(output="{}")


def test_usage_and_cost_maps_int_fields_only():  # spec 013 FR-4 / test_..._fr4
    usage_details, cost_details = tracing.usage_and_cost(
        {"input_tokens": 10, "output_tokens": 5, "stop_reason": "end_turn"}, 0.0032
    )

    assert usage_details == {"input_tokens": 10, "output_tokens": 5}
    assert cost_details == {"total": 0.0032}


def test_usage_and_cost_handles_missing_values():  # spec 013 FR-4
    usage_details, cost_details = tracing.usage_and_cost(None, None)

    assert usage_details is None
    assert cost_details is None
