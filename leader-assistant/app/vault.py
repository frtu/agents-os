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

import hashlib
import subprocess
from datetime import date
from pathlib import Path

from . import config

# Canonical subdirectories (spec 03-workspace §2, §3).
RAW_SUBDIRS = ("assets", "clippings", "docs", "notes", "transcripts")

# Foundation docs bootstrapped into vault/docs/ on create (spec 22 R1, spec 007 FR-9).
# Each is copied verbatim (immutable core) and paired with a mutable *-extension.md overlay.
FOUNDATION_DOCS = ("wiki-schema", "wiki-architecture")
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
    # SDK skill-discovery mirror (spec 005 FR-5, D5): the agent runtime scans
    # .claude/skills/<name>/SKILL.md, so imports drop a second link here.
    (workspace / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

    portal = vault / "wiki" / "portal.md"
    if not portal.exists():
        portal.write_text("# Portal\n\nMaster catalog — one line per page.\n")
    log = vault / "wiki" / "log.md"
    if not log.exists():
        log.write_text("# Log\n\nAppend-only operational record.\n")
    _bootstrap_foundation_docs(workspace)
    _bootstrap_tbd(workspace)
    _init_workspace_repo(workspace)
    return workspace


def _bootstrap_foundation_docs(workspace: Path) -> None:
    """Populate vault/docs/ with immutable core copies + mutable extensions (spec 22 R1/R2/R7).

    For each foundation doc: copy the source verbatim into ``vault/docs/<name>.md`` (the core,
    byte-identical to the skill library's ``references/`` — spec 007 FR-9/AC-12), and create
    ``<name>-extension.md`` in the spec 22 §4 format (header + Path-overrides / Added /
    Overridden / Removed sections) recording this workspace's path overrides (FR-10). Idempotent
    and non-destructive: never overwrites a non-empty core or an existing extension. Raises
    ``WorkspaceError`` if a source doc is missing/empty (spec 22 R1) rather than writing a 0-byte
    core, and re-copies an existing 0-byte core (self-heal).
    """
    docs = workspace / "vault" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    src_dir = config.foundation_docs_source()
    today = date.today().isoformat()
    for name in FOUNDATION_DOCS:
        core = docs / f"{name}.md"
        source = src_dir / f"{name}.md"
        # spec 22 R1 / spec 007 FR-9: the core is a NON-EMPTY verbatim copy of a real source doc.
        # Never fabricate an empty core — a 0-byte core with an empty-string hash makes the
        # extension look like the "full" file (the inversion bug). Fail loudly instead.
        if not source.is_file():
            raise WorkspaceError(
                f"foundation doc source not found: {source}. Set LEADER_FOUNDATION_DOCS_SOURCE "
                f"(or LEADER_SKILLS_SOURCE) to the skill library's second-brain/references directory."
            )
        content = source.read_text(encoding="utf-8")
        if not content.strip():
            raise WorkspaceError(f"foundation doc source is empty: {source}")
        # Self-heal: treat an existing 0-byte core (from a previously botched bootstrap) as absent.
        if not core.exists() or core.stat().st_size == 0:
            core.write_text(content, encoding="utf-8")  # verbatim copy (immutable core, R2)
        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        ext = docs / f"{name}-extension.md"
        if not ext.exists():
            ext.write_text(
                _extension_template(name, workspace.name, source, source_hash, today),
                encoding="utf-8",
            )


def _extension_template(
    name: str, workspace_name: str, source: Path, source_hash: str, copied: str
) -> str:
    """Render a *-extension.md in the spec 22 §4 format (header + fixed sections)."""
    title = name.replace("-", " ").title()
    return (
        "---\n"
        f"extends: {name}.md\n"
        f"source: {source.as_posix()}\n"
        f"source-hash: {source_hash}\n"
        f"copied: {copied}\n"
        "---\n\n"
        f"# {title} — {workspace_name} extension\n\n"
        f"> Overlays `{name}.md`. Extension wins on conflict (spec 22 R5). Do not edit the core.\n\n"
        "## Path overrides\n"
        "- `raw/` → `vault/raw/`\n"
        "- `wiki/` → `vault/wiki/`\n"
        "- index file: `wiki/index.md` → `vault/wiki/portal.md`\n\n"
        "## Added rules\n"
        "- (none yet)\n\n"
        "## Overridden rules\n"
        "- (none yet)\n\n"
        "## Removed/restricted rules\n"
        "- (none yet)\n"
    )


def _bootstrap_tbd(workspace: Path) -> None:
    """Create vault/wiki/tbd.md — the unprocessed-work backlog (spec 007 FR-14/FR-15).

    Sectioned by **topic & theme** (headings), not a flat list; the ingest workflow reads and
    updates it each run. Idempotent: never clobbers an existing backlog.
    """
    tbd = workspace / "vault" / "wiki" / "tbd.md"
    if tbd.exists():
        return
    tbd.write_text(
        "---\n"
        "title: To Be Done\n"
        "category: backlog\n"
        f"created: {date.today().isoformat()}\n"
        "status: active\n"
        "---\n\n"
        "# tbd — unprocessed changes to `vault/wiki/`\n\n"
        "> Backlog of unprocessed knowledge work, grouped by **topic & theme** (spec 007 FR-14/FR-15).\n"
        "> The ingest workflow reads this file, processes items, checks off/removes completed work,\n"
        "> and records newly-discovered work back under the right section.\n\n"
        "## Sources (capture → ingest)\n"
        "- (no captured sources awaiting ingest)\n\n"
        "## Concepts (patterns & technologies)\n"
        "- (none)\n\n"
        "## Synthesis (cross-topic articulation)\n"
        "- (none)\n",
        encoding="utf-8",
    )


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


def install_skill_link(workspace: Path, name: str, source: Path) -> Path:
    """Reference-link a shared skill into the workspace (spec 005 FR-5).

    Creates two symlinks to ``source``: the canonical ``skills/<name>`` (spec layout)
    and the SDK discovery mirror ``.claude/skills/<name>``. Idempotent — a dangling or
    stale link is replaced. Returns the canonical link path.
    """
    canonical = workspace / "skills" / name
    mirror = workspace / ".claude" / "skills" / name
    target = source.resolve()
    for link in (canonical, mirror):
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_symlink() or link.exists():
            if link.is_symlink() and link.resolve() == target:
                continue
            link.unlink()
        link.symlink_to(target, target_is_directory=True)
    return canonical


def list_installed_skill_names(workspace: Path) -> list[str]:
    """Installed skill names — entries under <workspace>/skills/ (spec 005 FR-3)."""
    skills = workspace / "skills"
    if not skills.is_dir():
        return []
    return sorted(p.name for p in skills.iterdir() if not p.name.startswith("."))


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
