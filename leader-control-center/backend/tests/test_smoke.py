"""Smoke tests over the real ASGI app (TestClient), asserting the wire contract
the frontend consumes: camelCase envelopes, board column keys, and problem+json
errors. The simulation loop is a background asyncio task, so TestClient's short
lifespan keeps the store deterministic for these assertions."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

BASE = "/api/v1"


def _client() -> TestClient:
    return TestClient(create_app())


def test_initiatives_board_shape() -> None:
    with _client() as client:
        resp = client.get(f"{BASE}/initiatives")
        assert resp.status_code == 200
        boards = resp.json()
        assert len(boards) == 3

        board = boards[0]
        # camelCase envelope + projection fields
        assert "initiative" in board
        assert "epicId" in board
        assert "openHumanRequests" in board
        assert set(board["columns"]) == {
            "Todo", "Ready", "Running", "Blocked", "Completed"
        }
        # Resource envelope on the initiative aggregate
        initiative = board["initiative"]
        for key in ("id", "version", "createdAt", "updatedAt"):
            assert key in initiative


def test_catalog_endpoints() -> None:
    with _client() as client:
        caps = client.get(f"{BASE}/capabilities")
        providers = client.get(f"{BASE}/providers")
        assert caps.status_code == 200 and providers.status_code == 200
        assert len(caps.json()) > 0
        assert len(providers.json()) > 0


def test_attention_and_notifications() -> None:
    with _client() as client:
        attention = client.get(f"{BASE}/attention")
        notifications = client.get(f"{BASE}/notifications")
        assert attention.status_code == 200
        assert notifications.status_code == 200
        assert isinstance(attention.json(), list)
        assert isinstance(notifications.json(), list)


def test_unknown_execution_returns_problem_json() -> None:
    with _client() as client:
        resp = client.get(f"{BASE}/executions/does_not_exist")
        assert resp.status_code == 404
        assert resp.headers["content-type"].startswith("application/problem+json")
        body = resp.json()
        assert body["status"] == 404
        assert body["title"] == "Not Found"


def test_websocket_accepts_connection() -> None:
    with _client() as client:
        with client.websocket_connect(f"{BASE}/stream") as ws:
            # Broadcast model ignores client frames; connection should stay open.
            ws.send_text('{"type":"subscribe"}')
