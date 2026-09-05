"""Workspace bootstrap-template copy + bootstrap.sh run (spec 03-workspace §1.1 / AC10)."""

from __future__ import annotations

import pytest

from app import capabilities, vault


@pytest.fixture
def fake_template(tmp_path, monkeypatch):
    """A throwaway bootstrap template whose bootstrap.sh drops a marker file when run."""
    template = tmp_path / "_workspace_"
    template.mkdir()
    (template / ".gitignore").write_text("vault/.obsidian\n", encoding="utf-8")
    (template / "bootstrap.sh").write_text(
        "#!/usr/bin/env bash\ncd \"$(dirname \"$0\")\"\ntouch bootstrap.ran\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LEADER_WORKSPACE_TEMPLATE", str(template))
    return template


def test_template_copied_and_bootstrap_run_on_create(fake_template):
    # spec 03-workspace AC10: template contents are copied and bootstrap.sh is run on create.
    capabilities.create_workspace("demo")
    ws = vault.resolve_workspace("demo")
    assert (ws / "bootstrap.sh").is_file()
    assert (ws / ".gitignore").read_text(encoding="utf-8") == "vault/.obsidian\n"
    assert (ws / "bootstrap.ran").exists()  # bootstrap.sh actually executed


def test_template_copy_does_not_overwrite_existing(fake_template):
    # spec 03-workspace §1.1: copy is idempotent/non-destructive.
    capabilities.create_workspace("demo")
    ws = vault.resolve_workspace("demo")
    (ws / ".gitignore").write_text("custom\n", encoding="utf-8")
    vault.scaffold_workspace(ws)  # re-scaffold: must not clobber the edited file
    assert (ws / ".gitignore").read_text(encoding="utf-8") == "custom\n"


def test_missing_template_is_noop(tmp_path, monkeypatch):
    # spec 03-workspace §1.1: a missing template folder degrades to a no-op, not a failure.
    monkeypatch.setenv("LEADER_WORKSPACE_TEMPLATE", str(tmp_path / "nope"))
    info = capabilities.create_workspace("demo")
    assert info.scaffolded
