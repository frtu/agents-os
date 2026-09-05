"""`.env` loading for LEADER_* config (spec 03-workspace §0).

The app loads a repo-root `.env` at startup so operators can set any LEADER_* var — including
the configurable workspace root — without exporting it. A real shell/CLI value must still win.
"""

from __future__ import annotations

from app import config


def test_load_env_file_sets_var_from_file(tmp_path, monkeypatch):  # spec 03-workspace §0
    """A var present only in `.env` is loaded into the environment."""
    monkeypatch.delenv("LEADER_WORKSPACE_ROOT", raising=False)
    env = tmp_path / ".env"
    env.write_text("LEADER_WORKSPACE_ROOT=./from-dotenv\n", encoding="utf-8")

    loaded = config.load_env_file(env)

    assert loaded == env
    assert config.workspace_root() == config.Path("from-dotenv")


def test_shell_value_wins_over_dotenv(tmp_path, monkeypatch):  # spec 03-workspace §0
    """override=False: an existing environment value beats `.env` (operator override)."""
    monkeypatch.setenv("LEADER_WORKSPACE_ROOT", str(tmp_path / "from-shell"))
    env = tmp_path / ".env"
    env.write_text("LEADER_WORKSPACE_ROOT=./from-dotenv\n", encoding="utf-8")

    config.load_env_file(env)

    assert config.workspace_root() == tmp_path / "from-shell"


def test_load_env_file_missing_is_noop(tmp_path):  # spec 03-workspace §0
    """A missing `.env` returns None and changes nothing."""
    assert config.load_env_file(tmp_path / "nope.env") is None
