"""Activity Definitions (specs/execution/activity-definitions.md): template
encoding, validation, CRUD over the API, render, and the webhook test against an
in-memory HTTP transport (no network)."""
from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.application.activities import ActivityDefinitionService
from app.domain import activity_template as tpl
from app.domain.activity_template import TemplateError
from app.main import create_app

BASE = "/api/v1/activity-definitions"
SCHEMA = {
    "type": "object",
    "required": ["topic"],
    "properties": {
        "topic": {"type": "string"},
        "count": {"type": "integer", "default": 3},
    },
}
WEBHOOK = {
    "name": "Notify", "kind": "Webhook", "input": SCHEMA,
    "url": "https://hooks.test/notify?q={{topic}}",
    "headers": {"Authorization": "Bearer ${env:HOOK_TOKEN}", "X-Topic": "{{topic}}"},
    "bodyTemplate": '{"topic": {{topic}}, "count": {{count}}}',
}
BASH = {
    "name": "Report", "kind": "Bash", "input": SCHEMA,
    "script": "echo {{topic}}\nfor i in $(seq {{count}}); do echo $i; done\n",
}


# -- template encoding ---------------------------------------------------------
def test_values_are_encoded_for_their_slot() -> None:
    values = {"topic": "a b'; rm -rf /", "count": 2}
    assert tpl.render_script("echo {{topic}}", values) == "echo 'a b'\"'\"'; rm -rf /'"
    assert tpl.render_url("https://x/?q={{topic}}", values) == "https://x/?q=a%20b%27%3B%20rm%20-rf%20%2F"
    body = tpl.render_body('{"t": {{topic}}, "n": {{count}}}', "application/json", values)
    assert json.loads(body) == {"t": "a b'; rm -rf /", "n": 2}
    assert tpl.render_body("t={{topic}}", "text/plain", values) == "t=a b'; rm -rf /"


def test_headers_resolve_env_only_when_sending() -> None:
    headers = {"Authorization": "Bearer ${env:TOKEN}"}
    assert tpl.render_headers(headers, {}) == headers  # preview keeps the reference
    assert tpl.render_headers(headers, {}, {"TOKEN": "s3cret"}.get) == {
        "Authorization": "Bearer s3cret"
    }
    with pytest.raises(TemplateError, match="TOKEN"):
        tpl.render_headers(headers, {}, {}.get)


def test_defaults_and_required() -> None:
    assert tpl.resolve_values(SCHEMA, {"topic": "x"}) == {"topic": "x", "count": 3}
    with pytest.raises(TemplateError, match="topic"):
        tpl.resolve_values(SCHEMA, {})


# -- API -----------------------------------------------------------------------
@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def _use_transport(client: TestClient, handler, env: dict | None = None) -> None:
    cc = client.app.state.control_center
    cc.activities = ActivityDefinitionService(
        cc.store,
        http=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
        env=(env or {}).get,
    )


def test_seeded_examples(client) -> None:
    names = {d["name"]: d["kind"] for d in client.get(BASE).json()}
    assert names == {"Disk usage report": "Bash", "Notify webhook": "Webhook"}


def test_crud_flow(client) -> None:
    created = client.post(BASE, json=WEBHOOK)
    assert created.status_code == 201
    body = created.json()
    act_id = body["id"]
    assert body["method"] == "POST" and body["timeoutSeconds"] == 30
    assert body["contentType"] == "application/json"

    patched = client.patch(f"{BASE}/{act_id}", json={"name": "Notify v2", "method": "PUT"})
    assert patched.status_code == 200
    assert (patched.json()["name"], patched.json()["method"], patched.json()["version"]) == (
        "Notify v2", "PUT", 2,
    )
    assert client.get(f"{BASE}/{act_id}").json()["url"] == WEBHOOK["url"]

    bash = client.post(BASE, json=BASH).json()
    assert bash["timeoutSeconds"] == 300

    assert client.delete(f"{BASE}/{act_id}").status_code == 204
    assert client.get(f"{BASE}/{act_id}").status_code == 404
    assert client.delete(f"{BASE}/{act_id}").status_code == 404


@pytest.mark.parametrize("payload, message", [
    ({**BASH, "script": "if then fi"}, "Bash syntax error"),
    ({**BASH, "script": "echo {{nope}}"}, "undeclared"),
    ({**BASH, "script": "  "}, "needs a script"),
    ({**WEBHOOK, "url": "ftp://x"}, "http"),
    ({**WEBHOOK, "bodyTemplate": '{"t": "hello {{topic}}"}'}, "not valid JSON"),
    ({**WEBHOOK, "bodyTemplate": '{"t": "${env:HOOK_TOKEN}"}'}, "only allowed in header values"),
    ({**WEBHOOK, "headers": {"X": "{{missing}}"}}, "undeclared"),
    ({**WEBHOOK, "name": " "}, "Name is required"),
    ({**WEBHOOK, "input": {"type": "array"}}, "JSON Schema object"),
])
def test_validation_errors(client, payload: dict, message: str) -> None:
    resp = client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text
    assert message in resp.json()["detail"]


def test_update_is_revalidated(client) -> None:
    act_id = client.post(BASE, json=BASH).json()["id"]
    resp = client.patch(f"{BASE}/{act_id}", json={"script": "echo {{other}}"})
    assert resp.status_code == 422
    assert client.get(f"{BASE}/{act_id}").json()["version"] == 1


def test_render_preview_masks_secrets(client) -> None:
    act_id = client.post(BASE, json=WEBHOOK).json()["id"]
    rendered = client.post(f"{BASE}/{act_id}/render", json={"input": {"topic": "q3 risk"}}).json()
    assert rendered["url"] == "https://hooks.test/notify?q=q3%20risk"
    assert rendered["headers"]["Authorization"] == "Bearer ${env:HOOK_TOKEN}"
    assert json.loads(rendered["body"]) == {"topic": "q3 risk", "count": 3}
    missing = client.post(f"{BASE}/{act_id}/render", json={"input": {}})
    assert missing.status_code == 422


def test_webhook_test_sends_rendered_request(client) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(method=request.method, url=str(request.url),
                    auth=request.headers["authorization"], body=json.loads(request.content))
        return httpx.Response(202, json={"ok": True})

    _use_transport(client, handler, {"HOOK_TOKEN": "s3cret"})
    act_id = client.post(BASE, json=WEBHOOK).json()["id"]
    result = client.post(f"{BASE}/{act_id}/test", json={"input": {"topic": "deploy"}}).json()
    assert result["status"] == 202 and json.loads(result["responseBody"]) == {"ok": True}
    assert seen == {
        "method": "POST", "url": "https://hooks.test/notify?q=deploy",
        "auth": "Bearer s3cret", "body": {"topic": "deploy", "count": 3},
    }
    # The echoed request never contains the secret.
    assert result["request"]["headers"]["Authorization"] == "Bearer ${env:HOOK_TOKEN}"


def test_webhook_test_reports_transport_errors_and_missing_secret(client) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    act_id = client.post(BASE, json=WEBHOOK).json()["id"]
    _use_transport(client, handler, {})
    no_secret = client.post(f"{BASE}/{act_id}/test", json={"input": {"topic": "x"}})
    assert no_secret.status_code == 422 and "HOOK_TOKEN" in no_secret.json()["detail"]

    _use_transport(client, handler, {"HOOK_TOKEN": "t"})
    result = client.post(f"{BASE}/{act_id}/test", json={"input": {"topic": "x"}}).json()
    assert result["status"] is None and "ConnectError" in result["error"]


def test_bash_cannot_be_test_run(client) -> None:
    act_id = client.post(BASE, json=BASH).json()["id"]
    resp = client.post(f"{BASE}/{act_id}/test", json={"input": {"topic": "x"}})
    assert resp.status_code == 422 and "worker" in resp.json()["detail"]
