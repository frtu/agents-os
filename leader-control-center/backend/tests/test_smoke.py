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


def test_initiatives_summary_shape() -> None:
    with _client() as client:
        resp = client.get(f"{BASE}/initiatives")
        assert resp.status_code == 200
        summaries = resp.json()
        assert len(summaries) == 3

        summary = summaries[0]
        # Lightweight list row: counts, no columns.
        assert "initiative" in summary
        assert "epicId" in summary
        assert "storyCount" in summary
        assert "openHumanRequests" in summary
        assert "columns" not in summary
        # Returned in ascending initiative order.
        assert [s["initiative"]["order"] for s in summaries] == [0, 1, 2]
        # Resource envelope on the initiative aggregate.
        initiative = summary["initiative"]
        for key in ("id", "version", "createdAt", "updatedAt", "order"):
            assert key in initiative


def test_initiative_board_shape() -> None:
    with _client() as client:
        first = client.get(f"{BASE}/initiatives").json()[0]["initiative"]["id"]
        resp = client.get(f"{BASE}/initiatives/{first}/board")
        assert resp.status_code == 200
        board = resp.json()
        assert board["initiative"]["id"] == first
        assert "epicId" in board
        assert "openHumanRequests" in board
        assert set(board["columns"]) == {
            "Todo", "Ready", "Running", "Blocked", "Completed"
        }
        # Unknown initiative -> 404 problem+json.
        assert client.get(f"{BASE}/initiatives/nope/board").status_code == 404


def test_create_and_reorder_initiatives() -> None:
    with _client() as client:
        created = client.post(
            f"{BASE}/initiatives", json={"title": "New", "description": "d"}
        )
        assert created.status_code == 201
        new_id = created.json()["id"]
        assert created.json()["order"] == 3  # appended after the 3 seeded

        # New initiative has a board (backing epic was created).
        assert client.get(f"{BASE}/initiatives/{new_id}/board").status_code == 200

        ids = [s["initiative"]["id"] for s in client.get(f"{BASE}/initiatives").json()]
        reversed_ids = ids[::-1]
        resp = client.post(
            f"{BASE}/initiatives/reorder", json={"initiativeIds": reversed_ids}
        )
        assert resp.status_code == 200
        result = resp.json()
        assert [s["initiative"]["order"] for s in result] == [0, 1, 2, 3]
        assert [s["initiative"]["id"] for s in result] == reversed_ids


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
