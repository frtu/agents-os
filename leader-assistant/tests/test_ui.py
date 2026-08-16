"""Tests for the web UI surface (feature 003-assistant-ui).

Covers the route wiring the spec fixes — UI at `/`, Swagger at `/api/`, REST
endpoints still under `/api/<resource>` — and the parity invariant that the UI is
a pure presentation layer: `app/ui.py` reaches the backend only over HTTP and
never imports the capability/vault layer (spec 003 FR-3/FR-10/AC-8, P9).
"""

from __future__ import annotations

import ast
import pathlib

UI_PATH = pathlib.Path(__file__).resolve().parent.parent / "app" / "ui.py"


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
