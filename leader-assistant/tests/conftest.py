"""Shared test fixtures.

Every test runs against a throwaway vault root under a pytest ``tmp_path`` so the
suite never writes into the project (or any real vault). Config resolves the root
from ``LEADER_VAULT_ROOT`` on each call, so setting the env var per-test is enough
to isolate state.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_vault_root(tmp_path, monkeypatch):
    """Point the app at a private, empty vault root for the duration of a test."""
    root = tmp_path / "vaults"
    root.mkdir()
    monkeypatch.setenv("LEADER_VAULT_ROOT", str(root))
    monkeypatch.delenv("LEADER_VAULT_PATH", raising=False)
    monkeypatch.delenv("LEADER_DEFAULT_VAULT", raising=False)
    return root


@pytest.fixture
def client() -> TestClient:
    from app.api import app

    return TestClient(app)


@pytest.fixture
def offline_agent(monkeypatch):
    """Force chat down its deterministic, no-LLM fallback path.

    Chat's routine answer normally streams from the ``claude-agent-sdk`` runtime,
    which is non-deterministic and needs credentials. Making the runtime report
    itself unavailable makes ``ask()`` answer via the ``query`` capability
    instead — reproducible and offline, while still exercising the full
    orchestration (persona, conversation store, citations, persistence).
    """
    from app import agent

    async def _unavailable(*_args, **_kwargs):
        raise agent.AgentUnavailable("forced offline for tests")
        yield  # pragma: no cover — marks this an async generator

    monkeypatch.setattr(agent, "run_stream", _unavailable)
