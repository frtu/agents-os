"""Tests for the agent's MCP capability-tool surface (feature 006-mcp-capability-tools).

Offline and deterministic: exercises the tool registry, blacklist filtering, workspace
binding, and the mutating handlers directly — no live agent runtime needed. The opt-in
live test (LEADER_LIVE_AGENT=1) covers AC-6 (a chat turn reaches list_available_skills).
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app import agent, capabilities, config

# The parity tool set the agent should expose by default (spec 006 AC-1).
EXPECTED_DEFAULT = {
    "query", "spec_read", "plan",
    "list_workspaces", "get_workspace_info", "lint", "wiki_tree",
    "list_conversations", "get_conversation", "conversation_status",
    "list_available_skills", "list_installed_skills",
    "ingest", "import_skill",
}


def _names(selector=None, citations=None):
    specs = agent._selected_specs(selector, citations if citations is not None else [], config.mcp_tool_blacklist())
    return {s.name for s in specs}


def _handler(name, selector, citations=None):
    specs = agent._capability_tool_specs(selector, citations if citations is not None else [])
    return next(s for s in specs if s.name == name).handler


def _payload(result):
    return json.loads(result["content"][0]["text"])


def test_default_tool_set_is_full_parity_minus_exclusions():
    # AC-1: default registration is the parity set; chat/upload/create_workspace absent.
    assert _names() == EXPECTED_DEFAULT
    assert "create_workspace" not in _names()
    assert "upload" not in _names()
    assert "chat" not in _names() and "ask" not in _names()


def test_chat_is_never_registered_even_with_empty_blacklist(monkeypatch):
    # AC-2: chat is a structural exclusion, independent of the blacklist.
    monkeypatch.setenv("LEADER_MCP_TOOL_BLACKLIST", "")
    assert config.mcp_tool_blacklist() == set()
    names = _names()
    assert "chat" not in names and "ask" not in names and "ask_stream" not in names
    # Everything else is admitted when the blacklist is emptied.
    assert EXPECTED_DEFAULT <= names


def test_blacklist_is_config_driven(monkeypatch):
    # AC-3: adding names to the env blacklist removes exactly those tools, from both the
    # selected specs and allowed_tools — proving the default is config, not a hardcode.
    monkeypatch.setenv("LEADER_MCP_TOOL_BLACKLIST", "lint, wiki_tree")
    specs = agent._selected_specs(None, [], config.mcp_tool_blacklist())
    names = {s.name for s in specs}
    assert "lint" not in names and "wiki_tree" not in names
    assert "query" in names  # untouched
    allowed = agent._allowed_tool_names(specs)
    assert "mcp__leader__lint" not in allowed
    assert "mcp__leader__query" in allowed


def test_tools_are_bound_to_active_workspace():
    # AC-4: a workspace supplied in tool args is ignored; the handler uses the bound one.
    capabilities.create_workspace("bound")
    result = asyncio.run(_handler("get_workspace_info", "bound")({"workspace": "other"}))
    info = _payload(result)
    assert info["name"] == "bound"  # not "other"


def test_ingest_handler_executes_and_commits(isolated_workspace_root):
    # AC-5: the ingest tool writes a wiki source and commits, in the active workspace.
    capabilities.create_workspace("demo")
    result = asyncio.run(
        _handler("ingest", "demo")({"title": "Note", "content": "hello world", "provenance": "notes"})
    )
    report = _payload(result)
    assert report["workspace"] == "demo"
    assert report["source_page"].startswith("vault/wiki/sources/")
    assert report["committed"] is True
    assert (isolated_workspace_root / "demo" / report["source_page"]).is_file()


def test_import_skill_handler_creates_reference_link(isolated_workspace_root):
    # AC-5: the import_skill tool reference-links a library skill into the workspace.
    capabilities.create_workspace("demo")
    result = asyncio.run(_handler("import_skill", "demo")({"name": "weekly-digest"}))
    report = _payload(result)
    assert report["name"] == "weekly-digest"
    assert (isolated_workspace_root / "demo" / "skills" / "weekly-digest").is_symlink()


def test_ingest_handler_refuses_raw_and_surfaces_error(isolated_workspace_root):
    # A capability error is surfaced as tool text, not raised (handler contract).
    result = asyncio.run(_handler("import_skill", "demo")({"name": "../evil"}))
    text = result["content"][0]["text"]
    assert text.startswith("error:")


def test_query_handler_surfaces_citations():
    # FR-5: citations returned by the query capability are surfaced to the caller.
    capabilities.create_workspace("demo")
    capabilities.ingest(
        capabilities.models.IngestRequest(workspace="demo", title="Widgets", content="widgets are blue", provenance="notes")
    )
    citations: list = []
    asyncio.run(_handler("query", "demo", citations)({"question": "widgets"}))
    assert citations and any("widgets" in c.excerpt.lower() or "Widgets" in c.page for c in citations)


def test_rest_surface_unchanged(client):
    # AC-7: the blacklist governs only the agent surface; REST routes are intact.
    paths = {getattr(r, "path", None) for r in client.app.routes}
    for p in ("/health", "/api/workspaces", "/api/ingest", "/api/query", "/api/skills", "/api/chat"):
        assert p in paths


@pytest.mark.skipif(
    __import__("os").getenv("LEADER_LIVE_AGENT") != "1",
    reason="opt-in: requires the claude CLI/credentials (set LEADER_LIVE_AGENT=1)",
)
def test_live_chat_lists_available_skills(client):
    # AC-6: a chat turn asking to list installable skills reaches list_available_skills.
    v = client.post("/api/workspaces", json={"name": "live"}).json()["name"]
    r = client.post("/api/chat", json={"workspace": v, "message": "what skills can I install?"})
    assert r.status_code == 200
    assert "weekly-digest" in r.json()["reply"].lower()
