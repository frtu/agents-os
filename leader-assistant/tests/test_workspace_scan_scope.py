"""Workspace-scoped search (spec 011 FR-52 / AC-33).

The agent's reads and searches — `Read`/`Glob`/`Grep` and read-only shell such as `ls`/`find`/`grep` —
run `auto` only inside the selected workspace (or the skill library root). Anything that reaches
beyond is announced `approval`, so it scores at the gate and pauses for the operator.
"""

from __future__ import annotations

import pytest

from app import agent, config, execution_gate
from app.workflow import score_operation


@pytest.fixture
def ws(tmp_path, monkeypatch):
    workspace = tmp_path / "Workspaces" / "demo"
    (workspace / "vault" / "wiki").mkdir(parents=True)
    library = tmp_path / "library"
    (library / "some-skill").mkdir(parents=True)
    monkeypatch.setenv("LEADER_SKILLS_SOURCE", str(library))
    return workspace


def _op(workspace, tool_name, tool_input):
    operation = agent._operation_for_tool(workspace, tool_name, tool_input)
    return operation, score_operation(operation)


def _assert_in_scope(workspace, tool_name, tool_input):
    operation, scored = _op(workspace, tool_name, tool_input)
    assert operation.tier == "auto", f"{tool_name} {tool_input} should stay auto"
    assert scored.score < config.gate_threshold()


def _assert_needs_approval(workspace, tool_name, tool_input):
    operation, scored = _op(workspace, tool_name, tool_input)
    assert operation.tier == "approval", f"{tool_name} {tool_input} should need approval"
    assert "outside the selected workspace" in operation.reversibility
    assert scored.score >= config.gate_threshold()


@pytest.mark.parametrize(
    "command",
    [
        "ls",
        "ls -la vault/wiki",
        "find . -name '*.md'",
        "grep -rn cost vault/",
        "tree vault/wiki | head -20",
        "cd vault && ls",
    ],
)
def test_search_inside_workspace_is_auto_fr52_ac33(ws, command):
    _assert_in_scope(ws, "Bash", {"command": command})


def test_absolute_path_inside_workspace_is_auto_fr52_ac33(ws):
    _assert_in_scope(ws, "Bash", {"command": f"find {ws}/vault -name '*.md'"})


@pytest.mark.parametrize(
    "command",
    [
        "find / -name secrets",
        "ls ..",
        "ls ../other-workspace",
        "cd .. && ls",
        "cd && ls",
        "grep -r cost ~/Documents",
        "ls $HOME",
        "rg cost /etc",
        "git -C /tmp log",
        "D=/etc; ls $D",
        "D=/etc; find ${D}/ssl -type f",
    ],
)
def test_search_outside_workspace_needs_approval_fr52_ac33(ws, command):
    _assert_needs_approval(ws, "Bash", {"command": command})


def test_mixed_inside_and_outside_needs_approval_fr52(ws):
    # Any single location outside is enough.
    _assert_needs_approval(ws, "Bash", {"command": "ls vault && ls /Users"})


def test_mkdir_outside_stays_auto_ac31_unchanged_fr52(ws):
    # FR-50/AC-31: a safe create is not a search, so scan scope does not apply to it.
    operation, _ = _op(ws, "Bash", {"command": "mkdir -p /tmp/elsewhere/x"})
    assert operation.tier == "auto"


def test_native_read_tools_inside_are_auto_fr52_ac33(ws):
    _assert_in_scope(ws, "Read", {"file_path": str(ws / "vault" / "wiki" / "portal.md")})
    _assert_in_scope(ws, "Read", {"file_path": "vault/wiki/portal.md"})
    _assert_in_scope(ws, "Grep", {"pattern": "cost"})
    _assert_in_scope(ws, "Grep", {"pattern": "cost", "path": "vault"})
    _assert_in_scope(ws, "Glob", {"pattern": "**/*.md"})
    _assert_in_scope(ws, "Glob", {"pattern": "*.md", "path": str(ws / "vault")})


def test_native_read_tools_outside_need_approval_fr52_ac33(ws, tmp_path):
    _assert_needs_approval(ws, "Read", {"file_path": str(tmp_path / "private.md")})
    _assert_needs_approval(ws, "Read", {"file_path": "../other/vault/wiki/portal.md"})
    _assert_needs_approval(ws, "Grep", {"pattern": "cost", "path": "/etc"})
    _assert_needs_approval(ws, "Glob", {"pattern": "/Users/**/*.md"})
    _assert_needs_approval(ws, "Glob", {"pattern": "../**/*.md"})
    _assert_needs_approval(ws, "Glob", {"pattern": "*.md", "path": str(tmp_path)})


def test_skill_library_root_is_in_scope_fr52(ws):
    # Skill instructions are the agent's own tooling (spec 005 FR-1), not a scan.
    library = config.skills_library_root()
    _assert_in_scope(ws, "Read", {"file_path": str(library / "some-skill" / "SKILL.md")})
    _assert_in_scope(ws, "Bash", {"command": f"ls {library}/some-skill"})


def test_symlink_out_of_workspace_is_resolved_fr52(ws, tmp_path):
    # A link into the library stays in scope; a link to anywhere else does not.
    (ws / "skills").mkdir()
    (ws / "skills" / "linked").symlink_to(config.skills_library_root() / "some-skill")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (ws / "sneaky").symlink_to(elsewhere)
    _assert_in_scope(ws, "Bash", {"command": "ls skills/linked"})
    _assert_needs_approval(ws, "Bash", {"command": "ls sneaky/"})


def test_scan_path_tokens_fr52():
    assert execution_gate.scan_path_tokens("ls ..") == ("..",)
    assert execution_gate.scan_path_tokens("cd") == ("~",)
    assert execution_gate.scan_path_tokens("mkdir -p /x/y && ls /z") == ("/z",)
    assert execution_gate.scan_path_tokens("ls") == ()
    # A variable the command assigns is substituted; one it never set stays unresolvable (outside).
    assert execution_gate.scan_path_tokens("R=vault/wiki; find $R -type f") == ("vault/wiki",)
    assert execution_gate.scan_path_tokens("find $HOME") == ("$HOME",)


def test_assigned_variable_inside_workspace_is_auto_fr52(ws):
    _assert_in_scope(ws, "Bash", {"command": "R=vault; find $R -type f | sort"})
    _assert_in_scope(ws, "Bash", {"command": f"R={ws}/vault; find $R/wiki -type f"})


class _AskingChecker:
    async def review(self, report):
        from app.workflow import Verdict

        return Verdict(decision="ask", reasoning="ask the operator", source="default")


def test_outside_scan_pauses_the_run_for_approval_fr52_ac33(ws):
    # End to end through layer 2: an in-workspace search runs; a wider scan pauses the run and waits
    # for the operator instead of executing.
    import asyncio

    from app.workflow import WorkflowRun

    run = WorkflowRun(objective="find cost notes", workspace="demo", checker=_AskingChecker())
    inside = agent._operation_for_tool(ws, "Bash", {"command": "grep -rn cost vault/"})
    outside = agent._operation_for_tool(ws, "Bash", {"command": "grep -rn cost ~/Documents"})

    assert asyncio.run(run.permit(inside)).allow is True
    assert asyncio.run(run.permit(outside)).allow is False
    assert run.awaiting is True
    assert run.pending_report is not None
