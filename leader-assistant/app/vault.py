"""Workspace resolver, scaffolder, and vault/raw/ write-guard (spec 03-workspace).

A workspace is a directory holding:
    <workspace>/skills/         installed skills (files/folders or reference-links)
    <workspace>/sessions/       short-term operational conversations
    <workspace>/vault/          ingestion root (the durable knowledge store)
        <workspace>/vault/raw/       immutable sources (never written by the assistant)
        <workspace>/vault/wiki/      durable knowledge workspace
        <workspace>/vault/output/    generated artifacts
plus vault/wiki/portal.md (catalog) and vault/wiki/log.md (append-only ledger).
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from . import config

# Canonical subdirectories (spec 03-workspace §2, §3).
RAW_SUBDIRS = ("assets", "clippings", "docs", "notes", "transcripts")
WIKI_SUBDIRS = (
    "sources/_daily_",
    "concepts/patterns",
    "concepts/technologies",
    "product/persona",
    "product/entities",
    "product/features",
    "product/specs",
    "people/roles",
    "people/members",
    "resources/tools",
    "projects",
    "synthesis",
)


class WorkspaceError(Exception):
    """Raised for workspace resolution or vault/raw/ write-guard violations."""


def resolve_workspace(selector: str | None = None) -> Path:
    """Resolve a workspace path from a selector or the configured default.

    Precedence: LEADER_WORKSPACE_PATH > <root>/<selector> > <root>/<default>.
    """
    explicit = config.explicit_workspace_path()
    if explicit is not None and selector is None:
        return explicit
    name = selector or config.default_workspace_name()
    return config.workspace_root() / name


def list_workspace_names() -> list[str]:
    root = config.workspace_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "vault" / "wiki").is_dir())


def is_scaffolded(workspace: Path) -> bool:
    return all((workspace / d).is_dir() for d in ("vault", "sessions", "skills"))


def scaffold_workspace(workspace: Path) -> Path:
    """Create workspace structure: skills/, sessions/, vault/{raw,wiki,output}/ with canonical subdirs."""
    vault = workspace / "vault"
    for sub in RAW_SUBDIRS:
        (vault / "raw" / sub).mkdir(parents=True, exist_ok=True)
    for sub in WIKI_SUBDIRS:
        (vault / "wiki" / sub).mkdir(parents=True, exist_ok=True)
    (vault / "output").mkdir(parents=True, exist_ok=True)
    (workspace / "sessions").mkdir(parents=True, exist_ok=True)
    (workspace / "skills").mkdir(parents=True, exist_ok=True)

    portal = vault / "wiki" / "portal.md"
    if not portal.exists():
        portal.write_text("# Portal\n\nMaster catalog — one line per page.\n")
    log = vault / "wiki" / "log.md"
    if not log.exists():
        log.write_text("# Log\n\nAppend-only operational record.\n")
    _init_workspace_repo(workspace)
    return workspace


def _init_workspace_repo(workspace: Path) -> None:
    """Make the workspace its OWN git repo (spec 03-workspace §7 ledger).

    A dedicated repo isolates the workspace ledger from any enclosing repo, so
    workspace commits can never pollute a parent project checkout.
    """
    if (workspace / ".git").exists():
        return
    try:
        subprocess.run(["git", "init", "-q", str(workspace)], capture_output=True, text=True)
        # Guarantee an identity so commits succeed even without global config.
        subprocess.run(
            ["git", "-C", str(workspace), "config", "user.name", "Leader Assistant"],
            capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(workspace), "config", "user.email", "assistant@leader.local"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        pass


def guard_write_path(workspace: Path, target: Path) -> None:
    """Reject any write under vault/raw/ (spec 03-workspace AC2, Constitution P2)."""
    raw = (workspace / "vault" / "raw").resolve()
    resolved = target.resolve()
    if resolved == raw or raw in resolved.parents:
        raise WorkspaceError(f"vault/raw/ is immutable; refusing to write {target}")


def append_log(workspace: Path, operation: str, title: str) -> None:
    """Append a line to the append-only vault/wiki/log.md (spec 03-workspace §6)."""
    log = workspace / "vault" / "wiki" / "log.md"
    guard_write_path(workspace, log)
    entry = f"\n## [{date.today().isoformat()}] {operation} | {title}\n"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(entry)
