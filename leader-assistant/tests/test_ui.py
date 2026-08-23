"""Tests for the web UI surface (feature 003-assistant-ui).

Covers the route wiring the spec fixes — UI at `/`, Swagger at `/api/`, REST
endpoints still under `/api/<resource>` — and the parity invariant that the UI is
a pure presentation layer: `app/ui.py` reaches the backend only over HTTP and
never imports the capability/vault layer (spec 003 FR-3/FR-10/AC-8, P9).
"""

from __future__ import annotations

import ast
import pathlib
import types

from app import ui

UI_PATH = pathlib.Path(__file__).resolve().parent.parent / "app" / "ui.py"


def _req(**params):
    """A minimal stand-in for gr.Request exposing dict-able query_params."""
    return types.SimpleNamespace(query_params=params)


def test_root_serves_web_ui(client):
    # AC-1: the root path is the startup surface (Gradio UI), not an API redirect.
    r = client.get("/")
    assert r.status_code == 200
    assert "gradio" in r.text.lower()


def test_swagger_relocated_to_api(client):
    # AC-2: Swagger UI is served at /api/ ...
    docs = client.get("/api")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower() or "openapi" in docs.text.lower()
    assert client.get("/openapi.json").status_code == 200


def test_api_endpoints_still_resolve(client):
    # AC-2: ... and the /api/<resource> endpoints are not shadowed by the docs route.
    assert client.get("/api/workspaces").status_code == 200
    created = client.post("/api/workspaces", json={"name": "demo"})
    assert created.status_code == 200
    # chat endpoint exists (unprocessable without a body proves it is routed, not 404)
    assert client.post("/api/chat", json={}).status_code == 422


def test_ui_module_imports_no_backend_layer():
    # AC-8: the UI must not import app.capabilities / app.vault (it calls /api/* only).
    tree = ast.parse(UI_PATH.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    forbidden = {"app.capabilities", "capabilities", "app.vault", "vault", ".capabilities", ".vault"}
    assert not (imported & forbidden), f"UI must not import backend layer: {imported & forbidden}"


def test_ui_client_targets_api_paths():
    # FR-3/FR-4/FR-6: the UI's HTTP calls go to /api/* paths.
    src = UI_PATH.read_text()
    assert "/api/workspaces" in src
    assert "/api/chat/stream" in src


# --- spec 004 deep-linkable URL state (FR-29/FR-30/FR-31, AC-14) --------------


def test_initial_restores_workspace_and_open_sidebar_from_url(monkeypatch):
    # FR-29: ?workspace=beta&sidebar=open restores that workspace active and opens the sidebar.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha", "beta"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    out = ui._initial(_req(workspace="beta", sidebar="open"))
    assert out[1] == "beta"           # active workspace state
    assert out[6]["open"] is True     # sidebar update opens


def test_initial_defaults_and_hides_sidebar_without_params(monkeypatch):
    # FR-29: absent params ⇒ default workspace, sidebar closed (FR-1 default).
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha", "beta"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    out = ui._initial(_req())
    assert out[1] == "alpha"
    assert out[6]["open"] is False


def test_initial_unknown_workspace_falls_back_to_default(monkeypatch):
    # FR-29: an unknown ?workspace falls back to the default workspace.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha", "beta"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    out = ui._initial(_req(workspace="ghost", sidebar="closed"))
    assert out[1] == "alpha"
    assert out[6]["open"] is False


def test_ui_wires_deep_link_navigation_and_silent_toggle():
    # FR-30: workspace select/create navigates to the deep-linked URL (full reload).
    # FR-31: sidebar toggle updates the URL silently via history.replaceState (no reload).
    src = UI_PATH.read_text()
    assert "window.location.href" in src          # FR-30 full reload
    assert "_NAV_WORKSPACE_JS" in src
    assert "history.replaceState" in src          # FR-31 silent update
    assert "sidebar.expand(" in src and "sidebar.collapse(" in src
    assert "searchParams.set('workspace'" in src
    assert "searchParams.set('sidebar'" in src


# --- spec 004 conversation deep-link (FR-32, AC-15) ---------------------------


def test_initial_restores_conversation_from_url(monkeypatch):
    # FR-32: ?conversation=<id> restores that thread into the chat, scoped to the active workspace.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    captured = {}

    def fake_detail(ws, cid):
        captured["args"] = (ws, cid)
        return {"messages": [{"role": "user", "text": "hi"},
                             {"role": "assistant", "text": "hello there"}]}

    monkeypatch.setattr(ui, "_get_session_detail", fake_detail)
    out = ui._initial(_req(workspace="alpha", conversation="conv-123"))
    assert captured["args"] == ("alpha", "conv-123")   # detail fetched, workspace-scoped
    chat_msgs, conv = out[7], out[8]
    assert conv == "conv-123"
    assert [m["content"] for m in chat_msgs] == ["hi", "hello there"]


def test_initial_unknown_conversation_starts_fresh(monkeypatch):
    # FR-32: an unknown/erroring ?conversation degrades to a fresh thread (greeting), not an error.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")

    def boom(ws, cid):
        raise RuntimeError("no such session")

    monkeypatch.setattr(ui, "_get_session_detail", boom)
    out = ui._initial(_req(workspace="alpha", conversation="ghost"))
    chat_msgs, conv = out[7], out[8]
    assert conv is None
    assert chat_msgs == [{"role": "assistant", "content": ui.GREETING}]


def test_initial_no_conversation_param_starts_fresh(monkeypatch):
    # FR-32: absent ?conversation ⇒ fresh thread, no session lookup.
    monkeypatch.setattr(ui, "_list_workspaces",
                        lambda: {"workspaces": ["alpha"], "default": "alpha"})
    monkeypatch.setattr(ui, "_wiki_html", lambda ws: "")
    monkeypatch.setattr(ui, "_get_session_detail",
                        lambda *a: (_ for _ in ()).throw(AssertionError("should not fetch")))
    out = ui._initial(_req(workspace="alpha"))
    assert out[8] is None
    assert out[7] == [{"role": "assistant", "content": ui.GREETING}]


def test_ui_wires_conversation_deep_link():
    # FR-32: session select / new chat / turn completion update ?conversation silently.
    src = UI_PATH.read_text()
    assert "_CONV_URL_JS" in src
    assert "searchParams.set('conversation'" in src
    assert "searchParams.delete('conversation'" in src   # New conversation clears it
