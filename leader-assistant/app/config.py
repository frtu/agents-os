"""Configuration + workspace resolution (spec 03-workspace §0, Constitution P13).

Environment overrides:
- LEADER_WORKSPACE_PATH    explicit single-workspace path (wins over root/selector)
- LEADER_WORKSPACE_ROOT    root directory holding Workspaces/<name>/ (default: ./Workspaces)
- LEADER_DEFAULT_WORKSPACE default workspace selector when none is supplied
- LEADER_SKILLS_SOURCE     shared skill library root (default: repo-sibling skills/)
- LEADER_FOUNDATION_DOCS_SOURCE  foundation-doc source dir (default: <skills>/second-brain/references)
- LEADER_MCP_TOOL_BLACKLIST comma-separated agent MCP tool names to withhold
- LEADER_AGENT_MODEL       Claude Agent SDK model selector (default: sonnet)
- LEADER_SETTINGS_PATH     runtime settings file (default: <workspace root>/.leader-settings.json)
"""

from __future__ import annotations

import json
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

    Resolution order: LEADER_SKILLS_SOURCE override, then the repo-local ``library/skills`` (this
    repo bundles its own skill library), then the ``skills/`` folder sibling to the repo. Returning
    a real directory matters because foundation-doc bootstrap now fails loudly on a missing source.
    """
    override = os.getenv("LEADER_SKILLS_SOURCE")
    if override:
        return Path(override).expanduser()
    repo = Path(__file__).resolve().parent.parent  # <repo>/app -> <repo>
    local = repo / "library" / "skills"
    if local.is_dir():
        return local
    return repo.parent / "skills"


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


DEFAULT_AGENT_MODEL = "sonnet"

# Curated offline fallback for the model picker (spec 004 FR-27). Aliases resolve to the
# latest model in each tier; the pinned IDs are the currently-known concrete versions. Used
# whenever the provider's /v1/models list is unreachable or uncredentialed.
STATIC_MODELS: tuple[tuple[str, str], ...] = (
    ("opus", "Claude Opus (latest)"),
    ("sonnet", "Claude Sonnet (latest)"),
    ("haiku", "Claude Haiku (latest)"),
    ("claude-opus-4-7", "Claude Opus 4.7"),
    ("claude-sonnet-4-6", "Claude Sonnet 4.6"),
    ("claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
)

_SETTINGS_MODEL_KEY = "agent_model"


def settings_path() -> Path:
    """File holding runtime, UI-selectable settings (spec 004 FR-28).

    Lives under the (git-ignored) workspace root by default so runtime state stays with
    the workspaces rather than the source tree. Overridable via ``LEADER_SETTINGS_PATH``.
    """
    override = os.getenv("LEADER_SETTINGS_PATH")
    if override:
        return Path(override).expanduser()
    return workspace_root() / ".leader-settings.json"


def _read_settings() -> dict:
    """Load the settings file, tolerant of a missing or corrupt file (returns ``{}``)."""
    path = settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_settings(data: dict) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def agent_model() -> str:
    """Model the Claude Agent SDK runtime uses (plan §Technical Context, spec 004 FR-28).

    Governs both the chat runtime (``app/agent.py``) and the ingest-activity runtime
    (``app/activity_ingest.py``) so a single knob selects the model for every agent surface.
    Precedence: the **persisted** setting (a UI selection) wins over env ``LEADER_AGENT_MODEL``,
    which wins over the ``sonnet`` default. Read fresh each call so a selection applies
    process-wide immediately. Blank values at any layer fall through to the next.
    """
    persisted = _read_settings().get(_SETTINGS_MODEL_KEY)
    if isinstance(persisted, str) and persisted.strip():
        return persisted.strip()
    raw = os.getenv("LEADER_AGENT_MODEL")
    if raw is None or not raw.strip():
        return DEFAULT_AGENT_MODEL
    return raw.strip()


def set_agent_model(value: str) -> str:
    """Persist the runtime model selection (spec 004 FR-28); returns the stored value."""
    value = (value or "").strip()
    if not value:
        raise ValueError("model must be a non-empty string")
    data = _read_settings()
    data[_SETTINGS_MODEL_KEY] = value
    _write_settings(data)
    return value


DEFAULT_INTERACTION_TIMEOUT = 30


def interaction_timeout_seconds() -> int:
    """Default countdown for an agent→user interaction card (spec 008 FR-9, D5).

    System-wide default is **30 seconds**, overridable via ``LEADER_INTERACTION_TIMEOUT``.
    A per-request override is applied at ``create_interaction`` time; this is the fallback.
    A non-positive or unparseable value falls back to the 30s default.
    """
    raw = os.getenv("LEADER_INTERACTION_TIMEOUT")
    if raw is None:
        return DEFAULT_INTERACTION_TIMEOUT
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_INTERACTION_TIMEOUT
    return value if value > 0 else DEFAULT_INTERACTION_TIMEOUT


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
