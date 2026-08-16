"""Unit tests for the agent's raw-guard PreToolUse decision (feature 005 FR-10).

The guard enforces vault/raw/ immutability (P2) for the autonomous agent, whose write
tools bypass ``can_use_tool`` under ``bypassPermissions``. These tests target the pure
``_raw_guard_decision`` helper — no SDK, no credentials — so the deny/allow mapping is
deterministic. Bash coverage is a heuristic (spec 005 D3: git is the backstop).
"""

from __future__ import annotations

from pathlib import Path

from app.agent import _raw_guard_decision

WS = Path("/tmp/ws")


def test_denies_write_under_vault_raw():
    reason = _raw_guard_decision(WS, "Write", {"file_path": str(WS / "vault" / "raw" / "notes" / "x.md")})
    assert reason and "raw" in reason.lower()


def test_denies_edit_under_vault_raw_relative_path():
    # A relative file_path resolves against the workspace cwd and is still caught.
    reason = _raw_guard_decision(WS, "Edit", {"file_path": "vault/raw/docs/y.md"})
    assert reason is not None


def test_denies_notebook_edit_under_vault_raw():
    reason = _raw_guard_decision(WS, "NotebookEdit", {"notebook_path": str(WS / "vault" / "raw" / "n.ipynb")})
    assert reason is not None


def test_allows_write_under_vault_wiki():
    assert _raw_guard_decision(WS, "Write", {"file_path": str(WS / "vault" / "wiki" / "page.md")}) is None


def test_allows_write_outside_workspace_raw():
    # A write elsewhere (e.g. output/) is not the raw-guard's concern.
    assert _raw_guard_decision(WS, "Write", {"file_path": str(WS / "vault" / "output" / "r.md")}) is None


def test_denies_obvious_bash_redirect_into_raw():
    reason = _raw_guard_decision(WS, "Bash", {"command": "echo hi > vault/raw/notes/x.md"})
    assert reason is not None


def test_allows_bash_read_of_raw():
    # Reading raw is fine; only writes are denied.
    assert _raw_guard_decision(WS, "Bash", {"command": "cat vault/raw/notes/x.md"}) is None


def test_allows_unrelated_bash():
    assert _raw_guard_decision(WS, "Bash", {"command": "ls -la"}) is None
