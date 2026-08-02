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


def test_create_story_lands_in_todo() -> None:
    with _client() as client:
        summary = client.get(f"{BASE}/initiatives").json()[0]
        init_id = summary["initiative"]["id"]
        epic_id = summary["epicId"]

        created = client.post(
            f"{BASE}/stories",
            json={
                "epicId": epic_id, "title": "Wire billing",
                "description": "d", "priority": 1,
                "acceptanceCriteria": ["invoices export", "taxes computed"],
            },
        )
        assert created.status_code == 201
        story = created.json()
        assert story["status"] == "Draft"
        assert story["epicId"] == epic_id
        assert [ac["description"] for ac in story["acceptanceCriteria"]] == [
            "invoices export", "taxes computed"
        ]

        # New Draft story shows up in the Todo column of that board.
        board = client.get(f"{BASE}/initiatives/{init_id}/board").json()
        todo_ids = [c["story"]["id"] for c in board["columns"]["Todo"]]
        assert story["id"] in todo_ids

        # Unknown epic -> 404.
        bad = client.post(
            f"{BASE}/stories", json={"epicId": "nope", "title": "x"}
        )
        assert bad.status_code == 404


def test_draft_story_prefills_fields() -> None:
    with _client() as client:
        init_id = client.get(f"{BASE}/initiatives").json()[0]["initiative"]["id"]
        resp = client.post(
            f"{BASE}/stories/draft",
            json={
                "initiativeId": init_id,
                "message": "Urgent: add SSO login.\n- support Google\n- support Okta",
            },
        )
        assert resp.status_code == 200
        draft = resp.json()
        assert draft["title"]
        assert draft["priority"] == 0  # "urgent" -> highest
        assert draft["acceptanceCriteria"] == ["support Google", "support Okta"]

        assert client.post(
            f"{BASE}/stories/draft", json={"initiativeId": "nope", "message": "x"}
        ).status_code == 404


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


def test_workflow_definition_crud() -> None:
    with _client() as client:
        # Seeded sample is present.
        listed = client.get(f"{BASE}/workflow-definitions")
        assert listed.status_code == 200
        names = [w["name"] for w in listed.json()]
        assert "Research Report" in names

        created = client.post(
            f"{BASE}/workflow-definitions",
            json={
                "name": "Onboarding",
                "input": {"type": "object", "required": ["team"],
                          "properties": {"team": {"type": "string"}}},
                "definition": "welcome(team)",
            },
        )
        assert created.status_code == 201
        wd = created.json()
        wd_id = wd["id"]
        for key in ("id", "version", "createdAt", "updatedAt"):
            assert key in wd

        patched = client.patch(
            f"{BASE}/workflow-definitions/{wd_id}", json={"name": "Onboarding v2"}
        )
        assert patched.status_code == 200
        assert patched.json()["name"] == "Onboarding v2"
        assert patched.json()["version"] == wd["version"] + 1

        deleted = client.delete(f"{BASE}/workflow-definitions/{wd_id}")
        assert deleted.status_code == 204
        assert client.get(f"{BASE}/workflow-definitions/{wd_id}").status_code == 404


def test_delete_referenced_workflow_definition_conflicts() -> None:
    with _client() as client:
        wd_id = client.get(f"{BASE}/workflow-definitions").json()[0]["id"]
        # Reference it from a new initiative.
        client.post(
            f"{BASE}/initiatives",
            json={"title": "Templated", "workflowDefinitionId": wd_id},
        )
        resp = client.delete(f"{BASE}/workflow-definitions/{wd_id}")
        assert resp.status_code == 409
        assert resp.headers["content-type"].startswith("application/problem+json")


def test_create_templated_story_requires_input() -> None:
    with _client() as client:
        wd_id = client.get(f"{BASE}/workflow-definitions").json()[0]["id"]
        epic_id = client.get(f"{BASE}/initiatives").json()[0]["epicId"]

        # Missing required "topic" -> 422.
        bad = client.post(
            f"{BASE}/stories",
            json={"epicId": epic_id, "title": "T",
                  "workflowDefinitionId": wd_id, "templateInput": {}},
        )
        assert bad.status_code == 422

        ok = client.post(
            f"{BASE}/stories",
            json={"epicId": epic_id, "title": "T",
                  "workflowDefinitionId": wd_id,
                  "templateInput": {"topic": "GenAI"}},
        )
        assert ok.status_code == 201
        story = ok.json()
        assert story["workflowDefinitionId"] == wd_id
        assert story["templateInput"] == {"topic": "GenAI"}


def test_websocket_accepts_connection() -> None:
    with _client() as client:
        with client.websocket_connect(f"{BASE}/stream") as ws:
            # Broadcast model ignores client frames; connection should stay open.
            ws.send_text('{"type":"subscribe"}')
