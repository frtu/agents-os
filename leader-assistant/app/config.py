"""Configuration + workspace resolution (spec 03-workspace §0, Constitution P13).

Environment overrides:
- LEADER_WORKSPACE_PATH    explicit single-workspace path (wins over root/selector)
- LEADER_WORKSPACE_ROOT    root directory holding Workspaces/<name>/ (default: ./Workspaces)
- LEADER_DEFAULT_WORKSPACE default workspace selector when none is supplied
- LEADER_SKILLS_SOURCE     shared skill library root (default: repo-sibling skills/)
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOT = "Workspaces"
DEFAULT_WORKSPACE_NAME = "_default_"


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
