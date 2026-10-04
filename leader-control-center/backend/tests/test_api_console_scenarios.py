"""API Console scenarios (_specs_/features/001-api-console): replays the request
sequences of frontend/src/features/console/scenarios.ts against the app, so a
backend change that would break a console scenario fails here first. Inputs
are derived from the seeded state, as the console does (spec 001 FR-9)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

BASE = "/api/v1"


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def _ok(resp, status: int = 200):
    assert resp.status_code == status, resp.text
    return resp.json() if resp.content else None


def _first_initiative(client: TestClient) -> dict:
    return _ok(client.get(f"{BASE}/initiatives"))[0]


def _template_input(schema: dict) -> dict:
    # Mirrors exampleFor() with a string placeholder: defaults, else a value per type.
    by_type = {"string": "Console test", "boolean": False, "integer": 0, "number": 0}
    out = {}
    for name, prop in (schema.get("properties") or {}).items():
        if "default" in prop:
            out[name] = prop["default"]
        elif "enum" in prop:
            out[name] = prop["enum"][0]
        else:
            out[name] = by_type.get(prop.get("type"), "")
    return out


def test_schedule_lifecycle_scenario_ac6_ac8(client) -> None:
    # spec 001 AC-6 / AC-8: preview → create → get → trigger → runs → pause → resume → archive.
    initiative_id = _first_initiative(client)["initiative"]["id"]
    wd_id = _ok(client.get(f"{BASE}/workflow-definitions"))[0]["id"]
    wd = _ok(client.get(f"{BASE}/workflow-definitions/{wd_id}"))
    spec = {"kind": "Interval", "every": "PT1H"}

    preview = _ok(client.post(f"{BASE}/schedules/preview", json={
        "initiativeId": initiative_id, "name": "Console test", "spec": spec,
    }))
    assert preview["sentence"] and preview["nextOccurrences"]

    view = _ok(client.post(f"{BASE}/schedules", json={
        "initiativeId": initiative_id, "name": "Console test",
        "workflowDefinitionId": wd_id, "templateInput": _template_input(wd["input"]),
        "spec": spec,
    }), 201)
    schedule_id = view["schedule"]["id"]
    assert _ok(client.get(f"{BASE}/schedules/{schedule_id}"))["schedule"]["status"] == "Active"

    run = _ok(client.post(f"{BASE}/schedules/{schedule_id}/trigger"))
    assert run["status"] != "FailedToStart", run.get("error")
    assert len(_ok(client.get(f"{BASE}/schedules/{schedule_id}/runs"))) >= 1

    for command, status in (("pause", "Paused"), ("resume", "Active"), ("archive", "Archived")):
        body = _ok(client.post(f"{BASE}/schedules/{schedule_id}/{command}"))
        assert body["schedule"]["status"] == status


def test_activity_definition_scenario_ac6_ac8(client) -> None:
    # spec 001 AC-6 / AC-8: create bash → render → get → delete leaves nothing behind.
    created = _ok(client.post(f"{BASE}/activity-definitions", json={
        "name": "Console test (bash)",
        "description": "Temporary — created by the API Console",
        "kind": "Bash",
        "input": {"type": "object", "properties": {"target": {"type": "string", "default": "world"}}},
        "script": "echo hello {{target}}",
    }), 201)
    act_id = created["id"]

    rendered = _ok(client.post(f"{BASE}/activity-definitions/{act_id}/render", json={"input": {"target": "console"}}))
    assert "console" in str(rendered)
    assert _ok(client.get(f"{BASE}/activity-definitions/{act_id}"))["name"] == "Console test (bash)"

    assert client.delete(f"{BASE}/activity-definitions/{act_id}").status_code == 204
    assert client.get(f"{BASE}/activity-definitions/{act_id}").status_code == 404


def test_story_execution_scenario_ac6(client) -> None:
    # spec 001 AC-6: create Story → start → execution → timeline → open decisions.
    epic_id = _first_initiative(client)["epicId"]
    story = _ok(client.post(f"{BASE}/stories", json={"epicId": epic_id, "title": "Console test story"}), 201)

    # rest-api.md says 202 for async execution; the API returns 200 (KD-2 in clarification.md).
    execution = _ok(client.post(f"{BASE}/stories/{story['id']}/start"))
    execution_id = execution["id"]
    assert _ok(client.get(f"{BASE}/executions/{execution_id}"))["id"] == execution_id
    assert isinstance(_ok(client.get(f"{BASE}/executions/{execution_id}/timeline")), list)
    assert isinstance(_ok(client.get(f"{BASE}/executions/{execution_id}/decisions")), list)


def test_workflow_definition_scenario_ac6_ac8(client) -> None:
    # spec 001 AC-6 / AC-8: create → get → update → delete leaves nothing behind.
    created = _ok(client.post(f"{BASE}/workflow-definitions", json={
        "name": "Console test", "input": {"type": "object", "properties": {}}, "definition": "",
    }), 201)
    wd_id = created["id"]
    assert _ok(client.get(f"{BASE}/workflow-definitions/{wd_id}"))["name"] == "Console test"
    assert _ok(client.patch(f"{BASE}/workflow-definitions/{wd_id}", json={"name": "Console test (edited)"}))["name"] == "Console test (edited)"
    assert client.delete(f"{BASE}/workflow-definitions/{wd_id}").status_code == 204
    assert client.get(f"{BASE}/workflow-definitions/{wd_id}").status_code == 404


def test_failing_step_reports_problem_detail_ac7(client) -> None:
    # spec 001 AC-7 / P9: the console stops on a non-2xx and shows `detail`, so it must name the cause.
    resp = client.post(f"{BASE}/schedules/does-not-exist/trigger")
    assert resp.status_code == 404
    assert "does-not-exist" in resp.json()["detail"]
