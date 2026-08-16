"""Configuration + vault resolution (spec 03-vault §0, Constitution P13).

Environment overrides:
- LEADER_VAULT_PATH    explicit single-vault path (wins over root/selector)
- LEADER_VAULT_ROOT    root directory holding Vaults/<name>/ (default: ./Vaults)
- LEADER_DEFAULT_VAULT default vault selector when none is supplied
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOT = "Vaults"
DEFAULT_VAULT_NAME = "default"


def vault_root() -> Path:
    override = os.getenv("LEADER_VAULT_ROOT")
    return Path(override).expanduser() if override else Path.cwd() / DEFAULT_ROOT


def explicit_vault_path() -> Path | None:
    override = os.getenv("LEADER_VAULT_PATH")
    return Path(override).expanduser() if override else None


def default_vault_name() -> str:
    return os.getenv("LEADER_DEFAULT_VAULT", DEFAULT_VAULT_NAME)
