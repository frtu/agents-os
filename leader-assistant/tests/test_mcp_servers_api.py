"""Tests for per-workspace external MCP servers (feature 014-workspace-mcp-servers).

Offline and deterministic: registration writes a plain `<ws>/.mcp.json`, so add/list/remove need
no network or CLI. The one runtime-wiring test (AC-5) patches the SDK's `query` to capture the
assembled options without spawning the `claude` CLI. The interactive OAuth browser round-trip
(AC-8) is a documented manual step, not asserted here.
"""

from __future__ import annotations

import asyncio
import json
import subprocess

import pytest

from app import capabilities, config
from app.vault import WorkspaceError

ATLASSIAN = "https://mcp.atlassian.com/v1/mcp"


def _make_workspace(name="demo"):
    assert capabilities.create_workspace(name).scaffolded
    return name


def test_add_list_remove_round_trip_fr1_fr4(isolated_workspace_root):
    # FR-1..FR-4: add writes the standard schema, list reads it back, remove drops exactly one.
    v = _make_workspace()
    info = capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)
    assert info.name == "atlassian" and info.url == ATLASSIAN and info.transport == "http"

    path = isolated_workspace_root / v / ".mcp.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"mcpServers": {"atlassian": {"type": "http", "url": ATLASSIAN}}}

    listed = capabilities.list_mcp_servers(v)
    assert [s.name for s in listed.servers] == ["atlassian"]

    capabilities.add_mcp_server(v, "linear", "https://mcp.linear.app/mcp")
    capabilities.remove_mcp_server(v, "atlassian")
    remaining = {s.name for s in capabilities.list_mcp_servers(v).servers}
    assert remaining == {"linear"}


def test_add_is_idempotent_fr2(isolated_workspace_root):
    # FR-2: re-adding the same name updates in place, never duplicates.
    v = _make_workspace()
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)
    capabilities.add_mcp_server(v, "atlassian", "https://mcp.atlassian.com/v2/mcp", transport="sse")
    servers = config.workspace_mcp_servers(isolated_workspace_root / v)
    assert list(servers) == ["atlassian"]
    assert servers["atlassian"] == {"type": "sse", "url": "https://mcp.atlassian.com/v2/mcp"}


def test_malformed_name_is_rejected_with_no_write_fr2(isolated_workspace_root):
    # FR-2: a bad name is bad input — reject and write nothing.
    v = _make_workspace()
    with pytest.raises(WorkspaceError):
        capabilities.add_mcp_server(v, "../evil", ATLASSIAN)
    assert not (isolated_workspace_root / v / ".mcp.json").exists()


def test_remove_absent_server_errors_fr4(isolated_workspace_root):
    # FR-4: removing a server that was never registered is an error, not a silent success.
    v = _make_workspace()
    with pytest.raises(WorkspaceError):
        capabilities.remove_mcp_server(v, "nope")


def test_mcp_config_tracked_and_auth_dir_ignored_fr5_fr7(isolated_workspace_root):
    # FR-5/FR-7: .mcp.json is committed to the workspace repo; .mcp-auth/ is git-ignored.
    v = _make_workspace()
    ws = isolated_workspace_root / v
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)

    # The registration is committed (revertible) — it shows in the workspace's own git log.
    log = subprocess.run(
        ["git", "-C", str(ws), "log", "--oneline"], capture_output=True, text=True
    )
    assert "register atlassian" in log.stdout
    tracked = subprocess.run(
        ["git", "-C", str(ws), "ls-files", ".mcp.json"], capture_output=True, text=True
    )
    assert tracked.stdout.strip() == ".mcp.json"

    # .mcp-auth/ is ignored: git check-ignore returns the path when it is ignored.
    auth = config.workspace_mcp_auth_dir(ws)
    auth.mkdir(parents=True, exist_ok=True)
    (auth / "token.json").write_text("{}", encoding="utf-8")
    ignored = subprocess.run(
        ["git", "-C", str(ws), "check-ignore", ".mcp-auth/token.json"],
        capture_output=True, text=True,
    )
    assert ignored.returncode == 0 and ".mcp-auth" in ignored.stdout


def test_login_returns_config_dir_and_command_fr8(isolated_workspace_root):
    # FR-8: login reports the exact CLAUDE_CONFIG_DIR and a runnable fallback command.
    v = _make_workspace()
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)
    info = capabilities.login_mcp_server(v, "atlassian")
    auth = config.workspace_mcp_auth_dir(isolated_workspace_root / v)
    assert info.config_dir == str(auth)
    assert str(auth) in info.command and "atlassian" in info.command
    assert info.authenticated is False  # no token captured yet (FR-9, no false positive)
    assert auth.is_dir()


def test_login_unregistered_server_errors_fr8(isolated_workspace_root):
    v = _make_workspace()
    with pytest.raises(WorkspaceError):
        capabilities.login_mcp_server(v, "atlassian")


def test_run_stream_sets_config_dir_and_allows_external_tools_fr10(
    isolated_workspace_root, monkeypatch
):
    # FR-10: a run for a workspace with a registered server points CLAUDE_CONFIG_DIR at that
    # workspace's .mcp-auth/ and admits mcp__<name>__* — asserted offline on the assembled options.
    import claude_agent_sdk

    from app import agent

    v = _make_workspace()
    ws = isolated_workspace_root / v
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)

    captured: dict = {}

    async def fake_query(prompt=None, options=None):
        import os

        captured["opts"] = options
        captured["config_dir"] = os.environ.get("CLAUDE_CONFIG_DIR")  # as the CLI would see it
        return
        yield  # pragma: no cover — marks this an async generator

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    monkeypatch.setattr(agent, "_BASE_CONFIG_DIR", None)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    async def drive():
        async for _ in agent.run_stream("sys", "hi", v, ws, None, []):
            pass

    asyncio.run(drive())

    assert captured["config_dir"] == str(config.workspace_mcp_auth_dir(ws))
    assert "mcp__atlassian__*" in captured["opts"].allowed_tools


def _capture_config_dir(monkeypatch, *, messages=(), error: Exception | None = None) -> dict:
    """Patch the SDK query to record CLAUDE_CONFIG_DIR at call time, then yield/raise as told."""
    import os

    import claude_agent_sdk

    seen: dict = {}

    async def fake_query(prompt=None, options=None):
        seen["config_dir"] = os.environ.get("CLAUDE_CONFIG_DIR")
        for m in messages:
            yield m
        if error is not None:
            raise error

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    return seen


def _drive(v, ws):
    from app import agent

    async def go():
        async for _ in agent.run_stream("sys", "hi", v, ws, None, []):
            pass

    asyncio.run(go())


def test_run_stream_without_servers_keeps_operator_config_dir_ac9_fr10(
    isolated_workspace_root, monkeypatch
):
    # spec 014 AC-9 / FR-10: no registered server → no relocation; the operator's login stays usable.
    import os

    from app import agent

    v = _make_workspace()
    ws = isolated_workspace_root / v
    monkeypatch.setattr(agent, "_BASE_CONFIG_DIR", "/operator/claude")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/operator/claude")
    seen = _capture_config_dir(monkeypatch)

    _drive(v, ws)

    assert seen["config_dir"] == "/operator/claude"
    assert os.environ["CLAUDE_CONFIG_DIR"] == "/operator/claude"
    assert config.agent_config_dir(ws) is None


def test_run_stream_restores_config_dir_after_run_and_error_ac10_fr15(
    isolated_workspace_root, monkeypatch
):
    # spec 014 AC-10 / FR-15: the relocation is scoped to the run — undone on success and on error,
    # so the ingest activity / judge never inherit a workspace's .mcp-auth/.
    import os

    from app import agent

    v = _make_workspace()
    ws = isolated_workspace_root / v
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)
    monkeypatch.setattr(agent, "_BASE_CONFIG_DIR", None)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    seen = _capture_config_dir(monkeypatch)
    _drive(v, ws)
    assert seen["config_dir"] == str(config.workspace_mcp_auth_dir(ws))
    assert "CLAUDE_CONFIG_DIR" not in os.environ

    seen = _capture_config_dir(monkeypatch, error=RuntimeError("boom"))
    with pytest.raises(agent.AgentUnavailable):
        _drive(v, ws)
    assert seen["config_dir"] == str(config.workspace_mcp_auth_dir(ws))
    assert "CLAUDE_CONFIG_DIR" not in os.environ


def test_run_stream_auth_failure_is_actionable_ac11_fr16(isolated_workspace_root, monkeypatch):
    # spec 014 AC-11 / FR-16 / P14: the CLI's "Not logged in" survives as the AgentUnavailable reason
    # (with config dir + remedy) instead of the SDK's opaque "returned an error result".
    from claude_agent_sdk import AssistantMessage, TextBlock

    from app import agent

    v = _make_workspace()
    ws = isolated_workspace_root / v
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)
    monkeypatch.setattr(agent, "_BASE_CONFIG_DIR", None)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    not_logged_in = AssistantMessage(
        content=[TextBlock(text="Not logged in · Please run /login")],
        model="sonnet",
        error="authentication_failed",
    )
    _capture_config_dir(
        monkeypatch,
        messages=[not_logged_in],
        error=Exception("Claude Code returned an error result: success"),
    )

    with pytest.raises(agent.AgentUnavailable) as exc:
        _drive(v, ws)

    reason = str(exc.value)
    assert "authentication_failed" in reason and "Not logged in" in reason
    assert str(config.workspace_mcp_auth_dir(ws)) in reason
    assert "claude /login" in reason and "CLAUDE_CODE_OAUTH_TOKEN" in reason
    assert "returned an error result" not in reason


def test_mcp_capabilities_are_blacklisted_from_agent_fr12():
    # FR-12: the agent cannot manage external servers or credentials — the four capabilities are
    # in the default MCP tool blacklist, so they are never registered as agent tools.
    from app import agent

    specs = agent._selected_specs(None, [], config.mcp_tool_blacklist())
    names = {s.name for s in specs}
    for cap in ("list_mcp_servers", "add_mcp_server", "remove_mcp_server", "login_mcp_server"):
        assert cap in config.DEFAULT_MCP_TOOL_BLACKLIST
        assert cap not in names


def test_effect_tiers_fr13():
    # FR-13: declared effect tiers — list/login auto, add/remove reversible (git-recoverable
    # .mcp.json edits committed to the workspace repo; see D5 for why add is not approval).
    assert capabilities.EFFECTS["list_mcp_servers"].tier == "auto"
    assert capabilities.EFFECTS["add_mcp_server"].tier == "reversible"
    assert capabilities.EFFECTS["remove_mcp_server"].tier == "reversible"
    assert capabilities.EFFECTS["login_mcp_server"].tier == "auto"


def test_mcp_routes_are_registered_fr14(client):
    # FR-14 / P9: all four MCP routes are reachable via /api/*.
    from app.api import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/workspaces/{selector}/mcp" in paths
    assert "/api/workspaces/{selector}/mcp/{name}" in paths
    assert "/api/workspaces/{selector}/mcp/{name}/login" in paths


def test_rest_add_writes_directly_fr13(client, isolated_workspace_root):
    # FR-13 (reversible tier): add is a git-recoverable .mcp.json edit, so REST writes it
    # directly (200, no 409 approval round-trip) and the registration lands immediately. The
    # privilege concern is covered structurally instead — see spec 014 D5.
    v = _make_workspace()
    r = client.post(f"/api/workspaces/{v}/mcp", json={"name": "atlassian", "url": ATLASSIAN})
    assert r.status_code == 200
    assert r.json()["name"] == "atlassian"
    assert (isolated_workspace_root / v / ".mcp.json").exists()


def test_rest_list_and_remove_fr3_fr4(client, isolated_workspace_root):
    # FR-3/FR-4 over REST: list reads back a registered server; delete removes it (reversible, no ask).
    v = _make_workspace()
    capabilities.add_mcp_server(v, "atlassian", ATLASSIAN)

    listed = client.get(f"/api/workspaces/{v}/mcp").json()
    assert [s["name"] for s in listed["servers"]] == ["atlassian"]

    r = client.delete(f"/api/workspaces/{v}/mcp/atlassian")
    assert r.status_code == 200
    assert client.get(f"/api/workspaces/{v}/mcp").json()["servers"] == []
