"""Shared test fixtures.

Every test runs against a throwaway workspace root under a pytest ``tmp_path`` so
the suite never writes into the project (or any real workspace). Config resolves
the root from ``LEADER_WORKSPACE_ROOT`` on each call, so setting the env var
per-test is enough to isolate state.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_workspace_root(tmp_path, monkeypatch):
    """Point the app at a private, empty workspace root for the duration of a test."""
    root = tmp_path / "workspaces"
    root.mkdir()
    monkeypatch.setenv("LEADER_WORKSPACE_ROOT", str(root))
    monkeypatch.delenv("LEADER_WORKSPACE_PATH", raising=False)
    monkeypatch.delenv("LEADER_DEFAULT_WORKSPACE", raising=False)
    return root


@pytest.fixture(autouse=True)
def skills_library(tmp_path, monkeypatch):
    """Point LEADER_SKILLS_SOURCE at a throwaway library of fake skills (feature 005).

    Keeps the skill catalog/import tests independent of the real shared library.
    """
    lib = tmp_path / "skills"
    for name, desc in (("weekly-digest", "Summarise the week"), ("triage", "Triage incoming items")):
        d = lib / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nDo the thing.\n",
            encoding="utf-8",
        )
    # The real shared library ships second-brain/references/{wiki-schema,wiki-architecture}.md —
    # the foundation-doc source (spec 007 D10 / spec 22 R1). Bootstrap now fails loudly on a missing
    # source, so the throwaway library must provide non-empty foundation docs like the real one.
    refs = lib / "second-brain" / "references"
    refs.mkdir(parents=True)
    (refs / "wiki-schema.md").write_text("# Wiki Schema CORE\n\nraw/ wiki/ layout.\n", encoding="utf-8")
    (refs / "wiki-architecture.md").write_text(
        "# Wiki Architecture CORE\n\nsix categories.\n", encoding="utf-8"
    )
    monkeypatch.setenv("LEADER_SKILLS_SOURCE", str(lib))
    return lib


JUDGE_STUB_REASONING = "stubbed judge recommendation for tests"


@pytest.fixture(autouse=True)
def offline_judge(monkeypatch):
    """Replace the risk agent's model call with one canned recommendation (spec 011 FR-15).

    The checker is an LLM, so left live it makes the suite non-deterministic and
    credential-dependent — two identical requests pause with differently-worded reasoning, and
    ``/api/chat`` and ``/api/chat/stream`` stop converging. Pinning the recommendation to a
    permissive ``approve`` keeps the *deterministic filter* as the thing under test: whether a turn
    runs or asks then depends only on cold start, the ceiling, precedent and trust mode (FR-17..
    FR-20), never on the model's mood. Permissive is the demanding choice — a stub that asked would
    pass the gating tests for the wrong reason.

    ``tests/test_judge.py`` injects its own ``ask_model``, so the real parse/fail-closed paths
    (FR-21) are still covered there.
    """
    import json

    from app import judge

    async def _canned(*_args, **_kwargs) -> str:
        return json.dumps(
            {"decision": "approve", "reasoning": JUDGE_STUB_REASONING, "confidence": 0.9}
        )

    monkeypatch.setattr(judge, "sdk_ask_model", _canned)


@pytest.fixture
def session_file():
    """Resolve a conversation's file by id, whatever the naming scheme (spec 012 FR-7).

    Tests assert on session *content*, not on the filename; going through the store's own resolver
    keeps them from encoding the layout a second time.
    """
    from app import conversation

    def resolve(workspace, conversation_id):
        path = conversation.path_for(workspace, conversation_id)
        assert path is not None, f"no session file for {conversation_id}"
        return path

    return resolve


@pytest.fixture
def client() -> TestClient:
    from app.api import app

    return TestClient(app)


@pytest.fixture
def ui_over_api(client, monkeypatch):
    """Route the UI's HTTP calls at the in-process app, keeping the UI an HTTP-only client (P9)."""
    import types

    import httpx

    from app import ui

    def get(url, **kw):
        return client.get(url, **{k: v for k, v in kw.items() if k != "timeout"})

    def post(url, **kw):
        return client.post(url, **{k: v for k, v in kw.items() if k != "timeout"})

    def async_client(**kw):
        # The UI's streaming turns must reach the in-process app too, not whatever happens to be
        # listening on the real port.
        kw["transport"] = httpx.ASGITransport(app=client.app)
        return httpx.AsyncClient(**kw)

    shim = types.SimpleNamespace(
        get=get, post=post, Timeout=httpx.Timeout, AsyncClient=async_client
    )
    monkeypatch.setattr(ui, "httpx", shim)
    return ui


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
