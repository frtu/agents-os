"""REST client for the backend console (spec 002 FR-9, FR-10).

The console is just another client of the public API: it reads `/api/v1` over
HTTP and never imports the application, infra, workflow or domain layers, so it
can never see or do more than the API allows. Every read is labelled so a
failure can say *what* was being read, with the API's status and Problem+JSON
`detail` (P9).
"""
from __future__ import annotations

from typing import Any

import httpx

API_PREFIX = "/api/v1"


class ApiError(Exception):
    """A failed read: the label of the read, the HTTP status (None when the API
    was unreachable) and the API's detail or the transport error."""

    def __init__(self, read: str, status: int | None, detail: str) -> None:
        self.read = read
        self.status = status
        self.detail = detail
        where = f"HTTP {status}" if status is not None else "API unreachable"
        super().__init__(f"Could not load {read} ({where}): {detail}")


def _detail(resp: httpx.Response) -> str:
    """Problem+JSON `detail` when present, else the (truncated) raw body."""
    try:
        body = resp.json()
    except ValueError:
        return resp.text[:300] or resp.reason_phrase
    if isinstance(body, dict):
        return str(body.get("detail") or body.get("title") or body)
    return str(body)[:300]


class ConsoleApi:
    """Read-only queries the console needs, one method per `/api/v1` read."""

    def __init__(self, http: httpx.Client) -> None:
        self.http = http

    def _get(self, read: str, path: str) -> Any:
        try:
            resp = self.http.get(f"{API_PREFIX}{path}")
        except httpx.HTTPError as e:  # spec 002 FR-10: keep the transport cause
            raise ApiError(read, None, f"{type(e).__name__}: {e}") from e
        if resp.status_code >= 400:
            raise ApiError(read, resp.status_code, _detail(resp))
        return resp.json()

    # -- Board -------------------------------------------------------------
    def initiatives(self) -> list[dict]:
        return self._get("initiatives", "/initiatives")

    def board(self, initiative_id: str) -> dict:
        return self._get(f"board of initiative {initiative_id}", f"/initiatives/{initiative_id}/board")

    def story_tasks(self, story_id: str) -> list[dict]:
        return self._get(f"tasks of story {story_id}", f"/stories/{story_id}/tasks")

    # -- Definitions -------------------------------------------------------
    def workflow_definitions(self) -> list[dict]:
        return self._get("workflow definitions", "/workflow-definitions")

    def workflow_definition(self, wd_id: str) -> dict:
        return self._get(f"workflow definition {wd_id}", f"/workflow-definitions/{wd_id}")

    def activity_definitions(self) -> list[dict]:
        return self._get("activity definitions", "/activity-definitions")

    def activity_definition(self, ad_id: str) -> dict:
        return self._get(f"activity definition {ad_id}", f"/activity-definitions/{ad_id}")

    def schedules(self) -> list[dict]:
        return self._get("schedules", "/schedules")

    def schedule(self, schedule_id: str) -> dict:
        return self._get(f"schedule {schedule_id}", f"/schedules/{schedule_id}")

    def schedule_runs(self, schedule_id: str) -> list[dict]:
        return self._get(f"runs of schedule {schedule_id}", f"/schedules/{schedule_id}/runs")

    # -- Executions --------------------------------------------------------
    def execution(self, execution_id: str) -> dict:
        return self._get(f"execution {execution_id}", f"/executions/{execution_id}")

    def timeline(self, execution_id: str) -> list[dict]:
        return self._get(f"timeline of execution {execution_id}", f"/executions/{execution_id}/timeline")

    def open_decisions(self, execution_id: str) -> list[dict]:
        return self._get(
            f"open decisions of execution {execution_id}", f"/executions/{execution_id}/decisions"
        )

    def notifications(self) -> list[dict]:
        return self._get("notifications", "/notifications")

    def attention(self) -> list[dict]:
        return self._get("attention queue", "/attention")


def default_api(base_url: str) -> ConsoleApi:
    """The console's own API over loopback HTTP (spec 002 FR-9)."""
    return ConsoleApi(httpx.Client(base_url=base_url.rstrip("/"), timeout=15.0))
