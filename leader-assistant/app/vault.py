"""Vault resolver, scaffolder, and raw/ write-guard (spec 03-vault).

A vault is a directory of Markdown files:
    <vault>/raw/       immutable sources (never written by the assistant)
    <vault>/wiki/      durable knowledge workspace
    <vault>/sessions/  short-term operational logs
    <vault>/output/    generated artifacts
plus wiki/portal.md (catalog) and wiki/log.md (append-only ledger).
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from . import config

# Canonical subdirectories (spec 03-vault §2, §3).
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


class VaultError(Exception):
    """Raised for vault resolution or write-guard violations."""


def resolve_vault(selector: str | None = None) -> Path:
    """Resolve a vault path from a selector or the configured default.

    Precedence: LEADER_VAULT_PATH > <root>/<selector> > <root>/<default>.
    """
    explicit = config.explicit_vault_path()
    if explicit is not None and selector is None:
        return explicit
    name = selector or config.default_vault_name()
    return config.vault_root() / name


def list_vault_names() -> list[str]:
    root = config.vault_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "wiki").is_dir())


def is_scaffolded(vault: Path) -> bool:
    return all((vault / d).is_dir() for d in ("raw", "wiki", "sessions", "output"))


def scaffold_vault(vault: Path) -> Path:
    """Create the four top-level dirs, canonical subdirs, portal.md and log.md."""
    for sub in RAW_SUBDIRS:
        (vault / "raw" / sub).mkdir(parents=True, exist_ok=True)
    for sub in WIKI_SUBDIRS:
        (vault / "wiki" / sub).mkdir(parents=True, exist_ok=True)
    (vault / "sessions").mkdir(parents=True, exist_ok=True)
    (vault / "output").mkdir(parents=True, exist_ok=True)

    portal = vault / "wiki" / "portal.md"
    if not portal.exists():
        portal.write_text("# Portal\n\nMaster catalog — one line per page.\n")
    log = vault / "wiki" / "log.md"
    if not log.exists():
        log.write_text("# Log\n\nAppend-only operational record.\n")
    _init_vault_repo(vault)
    return vault


def _init_vault_repo(vault: Path) -> None:
    """Make the vault its OWN git repo (spec 03-vault §7 ledger).

    A dedicated repo isolates the vault ledger from any enclosing repo, so
    vault commits can never pollute a parent project checkout.
    """
    if (vault / ".git").exists():
        return
    try:
        subprocess.run(["git", "init", "-q", str(vault)], capture_output=True, text=True)
        # Guarantee an identity so commits succeed even without global config.
        subprocess.run(
            ["git", "-C", str(vault), "config", "user.name", "Leader Assistant"],
            capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(vault), "config", "user.email", "assistant@leader.local"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        pass


def guard_write_path(vault: Path, target: Path) -> None:
    """Reject any write under raw/ (spec 03-vault AC2, Constitution P2)."""
    raw = (vault / "raw").resolve()
    resolved = target.resolve()
    if resolved == raw or raw in resolved.parents:
        raise VaultError(f"raw/ is immutable; refusing to write {target}")


def append_log(vault: Path, operation: str, title: str) -> None:
    """Append a line to the append-only wiki/log.md (spec 03-vault §6)."""
    log = vault / "wiki" / "log.md"
    guard_write_path(vault, log)
    entry = f"\n## [{date.today().isoformat()}] {operation} | {title}\n"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(entry)
