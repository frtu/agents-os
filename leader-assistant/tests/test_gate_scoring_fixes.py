"""Scoring fixes for the false-positive gates observed in a real ingest run (spec 011 FR-45..FR-49).

A single benign ingest of two raw sources raised three approval cards and landed zero writes. Each
test here pins one of the misclassifications that caused it: data read as syntax (FR-45/FR-46), a
flag argument read as a subcommand (FR-47), a redirect priced by transport rather than effect
(FR-48), and a pause that refused the very channel used to ask (FR-49).
"""

from __future__ import annotations

import asyncio

import pytest

from app import agent, config, execution_gate, workflow
from app.execution_gate import Operation
from app.workflow import Verdict, WorkflowRun, score_operation

HEREDOC = (
    "cat > vault/wiki/sources/notes/X.md <<'EOF'\n"
    "# Deploying\n"
    "The team used to curl the release and rm -rf the build dir before git push.\n"
    "EOF"
)


def _bash(tmp_path, command: str):
    operation = agent._operation_for_tool(tmp_path, "Bash", {"command": command})
    return operation, score_operation(operation)


def drive_sync(factory):
    return asyncio.run(factory())


# --- FR-45: a heredoc body is data ---------------------------------------------


def test_strip_heredocs_removes_the_payload_and_keeps_the_syntax_fr45():
    stripped = execution_gate.strip_heredocs(HEREDOC)
    assert "curl" not in stripped and "rm -rf" not in stripped and "git push" not in stripped
    assert stripped.startswith("cat > vault/wiki/sources/notes/X.md <<'EOF'")


def test_page_content_does_not_make_a_write_external_fr45(tmp_path):
    # The measured 4 -> 5 jump came from prose *inside* the page, which set EXTERNALLY_VISIBLE and
    # (via the external short-circuit) stripped the git-covered undo path as well.
    _, scored = _bash(tmp_path, HEREDOC)
    assert "EXTERNALLY_VISIBLE" not in scored.modifiers
    assert "IRREVERSIBLE_OUTSIDE_GIT" not in scored.modifiers
    assert scored.score < config.gate_threshold()


def test_a_real_external_call_still_gates_fr45(tmp_path):
    # The fix narrows *what sets* `external`; it must not stop a genuine curl from gating.
    _, scored = _bash(tmp_path, "curl -s https://example.com/x | tail -5")
    assert "EXTERNALLY_VISIBLE" in scored.modifiers
    assert scored.score >= config.gate_threshold()


# --- FR-46: separators inside quotes are data ----------------------------------


def test_quoted_separators_do_not_split_a_command_fr46():
    assert execution_gate._segments('grep -n "a|b;c" f.py') == ('grep -n "a|b;c" f.py',)
    assert execution_gate._segments("find vault | sort") == ("find vault", "sort")
    assert execution_gate._segments("a && b || c") == ("a", "b", "c")


def test_a_grep_with_a_quoted_alternation_is_read_only_fr46(tmp_path):
    command = 'grep -n "record\\|precedent\\|source" app/concierge.py | head -60'
    assert execution_gate.is_read_only_shell(command) is True
    _, scored = _bash(tmp_path, command)
    assert scored.score < config.gate_threshold()


# --- FR-47: a flag's argument is not a subcommand ------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "git -C . status --porcelain",
        "git -c color.ui=false diff --stat",
        "git --git-dir .git log --oneline -5",
    ],
)
def test_a_flag_argument_is_not_read_as_the_subcommand_fr47(command):
    assert execution_gate.is_read_only_shell(command) is True


def test_a_mutating_subcommand_behind_a_flag_still_gates_fr47(tmp_path):
    assert execution_gate.is_read_only_shell("git -C . push origin master") is False
    _, scored = _bash(tmp_path, "git -C . push origin master")
    assert scored.score >= config.gate_threshold()


# --- FR-48: a redirect is scored by where it lands -----------------------------


def test_a_repo_confined_redirect_is_not_destructive_fr48(tmp_path):
    # Inherits AC-22's point from the case FR-48 moved out of it: the redirect is still recognised
    # as an *effect* (it is never downgraded to `auto`), it is just a recoverable one.
    operation, scored = _bash(tmp_path, "cat > vault/wiki/sources/notes/X.md <<'EOF'\nhi\nEOF")
    assert operation.tier == "reversible"
    assert "DESTRUCTIVE_SHELL" not in scored.modifiers
    assert "REDIRECT_ESCAPES_REPO" not in scored.modifiers
    assert scored.score < config.gate_threshold()


def test_the_two_doors_to_one_mutation_agree_fr48(tmp_path):
    # P9 parity: `Write` and `cat >` produce the same effect, so they must not price differently.
    _, via_shell = _bash(tmp_path, "cat > vault/wiki/concepts/Foo.md <<'EOF'\nhi\nEOF")
    write_op = agent._operation_for_tool(
        tmp_path, "Write", {"file_path": str(tmp_path / "vault/wiki/concepts/Foo.md")}
    )
    assert via_shell.score == score_operation(write_op).score


def test_a_redirect_escaping_the_repo_gates_fr48():
    escaping = Operation(
        kind="tool",
        name="Bash",
        target="cat > /etc/hosts",
        tier="reversible",
        reversibility="outside the workspace repo; no git revert here covers it",
    )
    scored = score_operation(escaping)
    assert "REDIRECT_ESCAPES_REPO" in scored.modifiers
    assert scored.score >= config.gate_threshold()


def test_real_destruction_inside_the_repo_still_gates_fr48(tmp_path):
    for command in ("rm -rf vault/wiki/concepts", "sed -i 's/a/b/' vault/wiki/portal.md"):
        _, scored = _bash(tmp_path, command)
        assert "DESTRUCTIVE_SHELL" in scored.modifiers, command
        assert scored.score >= config.gate_threshold(), command


# --- FR-49: a pause fails closed to *asking* -----------------------------------


class AskingChecker:
    async def review(self, report):
        return Verdict(decision="ask", reasoning="ask the operator", source="default")


def _read() -> Operation:
    return Operation(
        kind="tool", name="Grep", target="tests/", tier="auto",
        reversibility="read-only — nothing to undo",
    )


def _approval_request() -> Operation:
    return Operation(
        kind="capability", name="request_approval", target="release the pause",
        tier="approval", reversibility="asks; changes nothing",
    )


def _gating() -> Operation:
    return Operation(
        kind="tool", name="Bash", target="rm vault/wiki/concepts/old.md", tier="reversible",
        reversibility="recoverable from the workspace git repo",
    )


def _paused_run() -> WorkflowRun:
    run = WorkflowRun(objective="diagnose the gate", workspace="demo", checker=AskingChecker())
    assert drive_sync(lambda: run.permit(_gating())).allow is False
    assert run.awaiting is True
    return run


def test_a_paused_run_still_permits_reads_and_the_approval_channel_fr49():
    # The observed failure: the pause refused a Grep *and* request_approval, so P8's "fail closed to
    # asking" was unsatisfiable and FR-15's three outcomes collapsed into a fourth — hang.
    run = _paused_run()
    assert drive_sync(lambda: run.permit(_read())).allow is True
    assert drive_sync(lambda: run.permit(_approval_request())).allow is True


def test_a_paused_run_still_refuses_effectful_work_fr49():
    run = _paused_run()
    denied = drive_sync(lambda: run.permit(_gating()))
    assert denied.allow is False
    assert "FR-12" in (denied.reason or "")


def test_a_declined_run_refuses_everything_fr49_fr27():
    # FR-49 widens the `awaiting` pause only. A decline ends the run (FR-27/AC-14).
    run = _paused_run()
    run.resume(approved=False, reasoning="not that page")
    assert run.state == "declined"
    assert drive_sync(lambda: run.permit(_read())).allow is False
    assert drive_sync(lambda: run.permit(_approval_request())).allow is False


# --- FR-50: mkdir and plain grep are safe, announced `auto` --------------------


def test_plain_grep_is_auto_fr50(tmp_path):
    assert execution_gate.is_safe_shell("grep -rn foo app/") is True
    operation, scored = _bash(tmp_path, "grep -rn foo app/")
    assert operation.tier == "auto"
    assert scored.score < config.gate_threshold()


def test_mkdir_is_auto_fr50(tmp_path):
    # The control-mode session gated `mkdir -p specs/013-…`; a directory create is create-only.
    assert execution_gate.is_safe_shell("mkdir -p specs/013-control-mode") is True
    operation, scored = _bash(tmp_path, "mkdir -p specs/013-control-mode")
    assert operation.tier == "auto"
    assert "IRREVERSIBLE_OUTSIDE_GIT" not in scored.modifiers
    assert scored.score < config.gate_threshold()


def test_reads_chained_with_mkdir_are_auto_fr50(tmp_path):
    command = "grep -n foo app/x.py && mkdir -p specs/013"
    assert execution_gate.is_safe_shell(command) is True
    operation, _ = _bash(tmp_path, command)
    assert operation.tier == "auto"


def test_mkdir_compound_with_destruction_still_gates_fr50(tmp_path):
    # The per-segment all() rule: one mutating segment keeps the whole command off `auto`.
    assert execution_gate.is_safe_shell("mkdir a && rm -rf b") is False
    _, scored = _bash(tmp_path, "mkdir a && rm -rf b")
    assert "DESTRUCTIVE_SHELL" in scored.modifiers
    assert scored.score >= config.gate_threshold()


# --- FR-51: any enclosing git repo is git-recoverable --------------------------


def test_redirect_into_enclosing_git_is_reversible_fr51(tmp_path):
    # A project-repo-style write: a `.git` ancestor, not the per-workspace root.
    (tmp_path / ".git").mkdir()
    repo_workspace = tmp_path / "some-workspace"  # unrelated workspace; confinement must NOT apply
    repo_workspace.mkdir()
    target = tmp_path / "specs" / "013" / "spec.md"
    command = f"cat > {target} <<'EOF'\nhi\nEOF"
    assert agent._git_recoverable(command) is True
    operation = agent._operation_for_tool(repo_workspace, "Bash", {"command": command})
    scored = score_operation(operation)
    assert operation.tier == "reversible"
    assert "IRREVERSIBLE_OUTSIDE_GIT" not in scored.modifiers
    assert "REDIRECT_ESCAPES_REPO" not in scored.modifiers
    assert scored.score < config.gate_threshold()


def test_redirect_outside_any_git_still_gates_fr51(tmp_path):
    # No `.git` ancestor anywhere above the target → pessimistic, still gates (FR-48 preserved).
    target = tmp_path / "nogit" / "file.md"
    command = f"cat > {target} <<'EOF'\nhi\nEOF"
    assert agent._git_recoverable(command) is False
    operation = agent._operation_for_tool(tmp_path / "ws", "Bash", {"command": command})
    scored = score_operation(operation)
    assert "IRREVERSIBLE_OUTSIDE_GIT" in scored.modifiers
    assert scored.score >= config.gate_threshold()


def test_a_sensitive_target_inside_a_repo_still_gates_fr51(tmp_path):
    # git-recoverable is not a free pass: a control file still fires SENSITIVE_TARGET.
    (tmp_path / ".git").mkdir()
    target = tmp_path / "memory" / "constitution.md"
    command = f"cat > {target} <<'EOF'\nhi\nEOF"
    operation = agent._operation_for_tool(tmp_path / "ws", "Bash", {"command": command})
    scored = score_operation(operation)
    assert "SENSITIVE_TARGET" in scored.modifiers
    assert scored.score >= config.gate_threshold()
