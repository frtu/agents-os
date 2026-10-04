"""Backend console (Gradio) — _specs_/features/002-backend-console/spec.md.

Offline: the console's `ConsoleApi` is given a FastAPI `TestClient` (an
`httpx.Client`), so every read goes through the real `/api/v1` routes in-process.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace

import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from app.ui import render
from app.ui.client import ConsoleApi
from app.ui.console import MENUS, build_console, initial_item

UI = Path(__file__).resolve().parent.parent / "app" / "ui"


def _client() -> TestClient:
    return TestClient(create_app())


def _refs(tree_html: str) -> set[str]:
    return set(re.findall(r"data-ref='([^']+)'", tree_html))


def test_console_mounted_at_ui_ac1() -> None:
    # spec 002 AC-1: /ui serves the console; Swagger and the REST API are unaffected.
    with _client() as client:
        page = client.get("/ui/")
        assert page.status_code == 200
        assert "text/html" in page.headers["content-type"]
        assert client.get("/api").status_code == 200
        resp = client.get("/api/v1/initiatives")
        assert resp.status_code == 200 and len(resp.json()) == 3
        # Problem+JSON 404s on the API are not swallowed by the mount.
        missing = client.get("/api/v1/executions/nope")
        assert missing.status_code == 404
        assert missing.headers["content-type"].startswith("application/problem+json")


def test_sidebar_menus_in_order_ac2() -> None:
    # spec 002 AC-2: Board, Definitions, Executions — in that order — plus a refresh control.
    with _client() as client:
        demo = build_console(ConsoleApi(client))
        components = demo.config["components"]
        accordions = [c["props"].get("label") for c in components if c["type"] == "accordion"]
        assert accordions[:3] == ["Board", "Definitions", "Executions"]
        assert [m[0] for m in MENUS] == ["Board", "Definitions", "Executions"]
        assert any(c["type"] == "sidebar" for c in components)
        assert any(c["props"].get("elem_id") == "lc-refresh" for c in components)


def test_board_tree_lists_initiatives_stories_tasks_ac3() -> None:
    # spec 002 AC-3: every Initiative, its Stories, and their Tasks are clickable entries.
    with _client() as client:
        api = ConsoleApi(client)
        refs = _refs(render.board_tree(api))
        for summary in client.get("/api/v1/initiatives").json():
            ini_id = summary["initiative"]["id"]
            assert f"initiative:{ini_id}" in refs
            board = client.get(f"/api/v1/initiatives/{ini_id}/board").json()
            for cards in board["columns"].values():
                for card in cards:
                    story_id = card["story"]["id"]
                    assert f"story:{ini_id}/{story_id}" in refs
                    for task in client.get(f"/api/v1/stories/{story_id}/tasks").json():
                        assert f"task:{story_id}/{task['id']}" in refs


def test_definitions_tree_lists_all_groups_ac4() -> None:
    # spec 002 AC-4: Workflows, Activities and Schedules groups with every definition.
    with _client() as client:
        api = ConsoleApi(client)
        created = client.post("/api/v1/schedules", json={
            "initiativeId": "init_promo", "name": "Nightly report",
            "workflowDefinitionId": "wfd_research_report", "templateInput": {"topic": "x"},
            "spec": {"kind": "Interval", "every": "PT1H"},
        })
        assert created.status_code == 201, created.text
        refs = _refs(render.definitions_tree(api))
        assert {"group:workflows", "group:activities", "group:schedules"} <= refs
        for wd in client.get("/api/v1/workflow-definitions").json():
            assert f"workflow:{wd['id']}" in refs
        for ad in client.get("/api/v1/activity-definitions").json():
            assert f"activity:{ad['id']}" in refs
        assert f"schedule:{created.json()['schedule']['id']}" in refs


def test_executions_tree_lists_runtime_groups_ac5() -> None:
    # spec 002 AC-5: Executions, Notifications, Attention — started execution + open requests.
    with _client() as client:
        api = ConsoleApi(client)
        execution = client.post("/api/v1/stories/story_achievements/start").json()
        refs = _refs(render.executions_tree(api))
        assert {"group:executions", "group:notifications", "group:attention"} <= refs
        assert f"execution:{execution['id']}" in refs
        for request in client.get("/api/v1/attention").json():
            assert f"attention:{request['id']}" in refs
        for notification in client.get("/api/v1/notifications").json():
            assert f"notification:{notification['id']}" in refs


def test_open_each_kind_shows_summary_and_json_ac6() -> None:
    # spec 002 AC-6: one entry of every kind opens with a title, key fields, and raw JSON.
    expected = {
        "initiative": "Stories per column",
        "story": "Acceptance criteria",
        "task": "Planning mode",
        "workflow": "Definition",
        "activity": "Kind",
        "schedule": "Next occurrences",
        "execution": "Timeline",
        "notification": "Status",
        "attention": "Priority",
    }
    with _client() as client:
        api = ConsoleApi(client)
        client.post("/api/v1/schedules", json={
            "initiativeId": "init_promo", "name": "Nightly report",
            "workflowDefinitionId": "wfd_research_report", "templateInput": {"topic": "x"},
            "spec": {"kind": "Interval", "every": "PT1H"},
        })
        refs = (
            _refs(render.board_tree(api))
            | _refs(render.definitions_tree(api))
            | _refs(render.executions_tree(api))
        )
        for kind, marker in expected.items():
            ref = next(r for r in sorted(refs) if r.startswith(f"{kind}:"))
            title, body, raw = render.open_ref(api, ref)
            assert title.startswith("### ") and "⚠️" not in title, (ref, body)
            assert marker in body, (ref, body)
            assert raw, ref


def test_group_header_opens_table_ac7() -> None:
    # spec 002 AC-7: a group header opens a table of its entries.
    with _client() as client:
        api = ConsoleApi(client)
        for name in render.GROUPS:
            title, body, raw = render.open_ref(api, f"group:{name}")
            assert f"({len(raw)})" in title
            if raw:
                assert body.startswith("| ") and "|---|" in body
            else:
                assert body == "_None._"


def test_console_uses_rest_api_only_ac8() -> None:
    # spec 002 AC-8 (FR-9): the console reads the public API only — no layer shortcuts.
    forbidden = ("app.application", "app.infra", "app.workflow", "app.domain", "app.api")
    offenders = []
    for path in sorted(UI.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            mods = (
                [a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
            )
            offenders += [(path.name, m) for m in mods if m.startswith(forbidden)]
    assert offenders == []


def test_failed_read_names_read_status_detail_ac9() -> None:
    # spec 002 AC-9: an API rejection names the read, status and Problem+JSON detail ...
    with _client() as client:
        title, body, raw = render.open_ref(ConsoleApi(client), "execution:nope")
        assert "⚠️" in title and raw is None
        assert "execution nope" in body and "HTTP 404" in body and "Execution not found" in body
    # ... and an unreachable API names the read and the transport error, in place in the tree.
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    down = ConsoleApi(httpx.Client(base_url="http://console.test", transport=httpx.MockTransport(refuse)))
    tree = render.board_tree(down)
    assert "lc-error" in tree and "initiatives" in tree
    assert "API unreachable" in tree and "connection refused" in tree
    defs = render.definitions_tree(down)
    assert defs.count("lc-error") == 3


def test_deep_link_opens_entry_ac10() -> None:
    # spec 002 AC-10: ?item= on load selects that entry.
    request = SimpleNamespace(query_params={"item": "initiative:init_promo"})
    assert initial_item(request) == "initiative:init_promo"
    assert initial_item(SimpleNamespace(query_params={})) == ""
    with _client() as client:
        title, _, _ = render.open_ref(ConsoleApi(client), initial_item(request))
        assert title == "### 🎯 Promotion to Staff Engineer"
        assert render.open_ref(ConsoleApi(client), initial_item(None)) == render.HOME
