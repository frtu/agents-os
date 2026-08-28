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
