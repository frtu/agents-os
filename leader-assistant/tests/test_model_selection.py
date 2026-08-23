"""Model-selection feature (spec 004 FR-26..FR-28).

Offline and deterministic: no test hits the provider. `ANTHROPIC_API_KEY` is unset so
`available_models()` always takes the static-fallback path, and the persisted settings file
lives under the per-test workspace root (autouse `isolated_workspace_root`), so selections
never leak between tests or into the real project.
"""

from __future__ import annotations

import pytest

from app import capabilities, config


@pytest.fixture(autouse=True)
def _no_provider(monkeypatch):
    # Force the offline/static path (FR-27) and a clean env-model default for every test here.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LEADER_AGENT_MODEL", raising=False)


# --- config precedence (FR-28) ---------------------------------------------


def test_agent_model_precedence_persisted_over_env_over_default(monkeypatch):
    # spec 004 FR-28: persisted selection > env LEADER_AGENT_MODEL > "sonnet" default.
    assert config.agent_model() == "sonnet"  # nothing set → default
    monkeypatch.setenv("LEADER_AGENT_MODEL", "haiku")
    assert config.agent_model() == "haiku"  # env override
    config.set_agent_model("opus")
    assert config.agent_model() == "opus"  # persisted wins over env


def test_set_agent_model_persists_to_settings_file():
    # spec 004 FR-28: the choice is written to the settings file so it survives a restart.
    config.set_agent_model("opus")
    assert config.settings_path().is_file()
    assert config.agent_model() == "opus"


def test_set_agent_model_rejects_blank():
    with pytest.raises(ValueError):
        config.set_agent_model("   ")


# --- capability (FR-27) -----------------------------------------------------


def test_available_models_static_fallback_when_offline():
    # spec 004 FR-27: no credentials → curated static list, source="static", current present.
    out = capabilities.available_models()
    assert out.source == "static"
    ids = {m.id for m in out.models}
    assert {"opus", "sonnet", "haiku"} <= ids
    assert out.current in ids  # the active model always appears in the list


def test_set_active_model_reflected_by_capability_and_config():
    # spec 004 FR-28: selecting flows through to both agent_model() and the picker payload.
    out = capabilities.set_active_model("opus")
    assert out.current == "opus"
    assert config.agent_model() == "opus"
    assert capabilities.available_models().current == "opus"


def test_set_active_model_blank_raises_workspace_error():
    from app.vault import WorkspaceError

    with pytest.raises(WorkspaceError):
        capabilities.set_active_model("")


# --- REST parity (FR-28, P9) ------------------------------------------------


def test_rest_get_and_post_models(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.get("/api/models")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "static"
    assert body["current"] == "sonnet"

    r2 = client.post("/api/models", json={"model": "opus"})
    assert r2.status_code == 200
    assert r2.json()["current"] == "opus"

    # Persisted → a fresh GET still reports opus (survives beyond the one request).
    assert client.get("/api/models").json()["current"] == "opus"


def test_rest_post_models_rejects_blank(client):
    r = client.post("/api/models", json={"model": ""})
    assert r.status_code == 400
