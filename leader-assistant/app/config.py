"""Configuration + workspace resolution (spec 03-workspace §0, Constitution P13).

Environment overrides:
- LEADER_WORKSPACE_PATH    explicit single-workspace path (wins over root/selector)
- LEADER_WORKSPACE_ROOT    root directory holding Workspaces/<name>/ (default: ./Workspaces)
- LEADER_DEFAULT_WORKSPACE default workspace selector when none is supplied
- LEADER_SKILLS_SOURCE     shared skill library root (default: repo-sibling skills/)
- LEADER_FOUNDATION_DOCS_SOURCE  foundation-doc source dir (default: <skills>/second-brain/references)
- LEADER_MCP_TOOL_BLACKLIST comma-separated agent MCP tool names to withhold
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOT = "Workspaces"
DEFAULT_WORKSPACE_NAME = "_default_"

# Agent MCP tools withheld by default (spec 006 FR-1): the chat surface (recursion),
# the human-only raw upload channel (P2), and cross-workspace creation.
DEFAULT_MCP_TOOL_BLACKLIST = frozenset({"chat", "upload", "create_workspace"})


def workspace_root() -> Path:
    override = os.getenv("LEADER_WORKSPACE_ROOT")
    return Path(override).expanduser() if override else Path.cwd() / DEFAULT_ROOT


def explicit_workspace_path() -> Path | None:
    override = os.getenv("LEADER_WORKSPACE_PATH")
    return Path(override).expanduser() if override else None


def default_workspace_name() -> str:
    return os.getenv("LEADER_DEFAULT_WORKSPACE", DEFAULT_WORKSPACE_NAME)


def skills_library_root() -> Path:
    """Shared skill library root (spec 005 FR-1).

    Default: the ``skills/`` folder sibling to this repo (``agents-os-frtu/skills``),
    i.e. two parents up from ``app/``. Overridable via LEADER_SKILLS_SOURCE.
    """
    override = os.getenv("LEADER_SKILLS_SOURCE")
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parent.parent.parent / "skills"


def foundation_docs_source() -> Path:
    """Directory the foundation docs are bootstrapped from (spec 007 FR-9/D10, spec 22 R1).

    Default: the skill library's ``second-brain/references/`` — the source the
    ``second-brain-ingest`` skill was authored against (``wiki-schema.md`` /
    ``wiki-architecture.md``). Overridable via LEADER_FOUNDATION_DOCS_SOURCE.
    """
    override = os.getenv("LEADER_FOUNDATION_DOCS_SOURCE")
    if override:
        return Path(override).expanduser()
    return skills_library_root() / "second-brain" / "references"


def mcp_tool_blacklist() -> set[str]:
    """Agent MCP tool names withheld from the agent (spec 006 FR-1).

    Env `LEADER_MCP_TOOL_BLACKLIST` is a comma-separated list, tolerant of whitespace
    and empty entries. An explicit empty value (``""``) opts everything in; when the
    variable is unset the default ``{chat, upload, create_workspace}`` applies. Governs
    only the agent MCP surface, never REST (spec 006 FR-7).
    """
    raw = os.getenv("LEADER_MCP_TOOL_BLACKLIST")
    if raw is None:
        return set(DEFAULT_MCP_TOOL_BLACKLIST)
    return {name.strip() for name in raw.split(",") if name.strip()}
