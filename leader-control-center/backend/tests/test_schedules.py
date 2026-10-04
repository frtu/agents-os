"""Schedules (specs/planning/schedules.md): spec math, the firing algorithm with
an injected clock (no Temporal), the in-process adapter, and the API surface."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.application.errors import InvariantError
from app.application.schedules import ScheduleService
from app.application.service import ControlCenter, build_control_center
from app.domain import schedule_spec
from app.domain.enums import (
    OverlapPolicy,
    PlanningStatus,
    SchedulePauseReason,
    ScheduleRunStatus,
    ScheduleStatus,
    StoryExecutionStatus,
)
from app.domain.models import ScheduleSpec
from app.domain.schedule_spec import SpecError
from app.infra.db import Database
from app.infra.store import Store
from app.main import create_app
from app.workflow.in_process_scheduler import InProcessScheduler

BASE = "/api/v1"
INITIATIVE = "init_promo"
WFD = "wfd_research_report"  # seeded; requires `topic`
T0 = datetime(2026, 10, 5, 7, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at

    def advance(self, **kwargs) -> datetime:
        self.at += timedelta(**kwargs)
        return self.at


@pytest.fixture
def env():
    cc: ControlCenter = build_control_center()
    clock = Clock(T0)
    adapter = InProcessScheduler(cc.store, clock)
    cc.schedules = ScheduleService(cc, adapter, clock)
    return cc, cc.schedules, clock, adapter


def _hourly(svc: ScheduleService, **kwargs):
    # Created at T0 (anchor = created_at); occurrences every hour after.
    return svc.create(
        INITIATIVE, "Hourly digest", WFD, {"topic": "risk"},
        ScheduleSpec(kind="Interval", every="PT1H", anchor="2026-10-05T07:00:00Z"),
        **kwargs,
    ).schedule


def _runs(svc: ScheduleService, schedule_id: str):
    return list(reversed(svc.runs(schedule_id)))  # oldest first


def _finish(cc: ControlCenter, story_id: str, status: StoryExecutionStatus) -> None:
    execution = cc.store.executions[cc.store.execution_by_story[story_id]]
    execution.status = status


# -- spec math -----------------------------------------------------------------
def test_interval_next_and_latest() -> None:
    spec = ScheduleSpec(kind="Interval", every="PT1H", anchor="2026-10-05T07:00:00Z")
    nxt = schedule_spec.next_occurrences(spec, T0 + timedelta(minutes=10), 2, T0)
    assert nxt == [T0 + timedelta(hours=1), T0 + timedelta(hours=2)]
    assert schedule_spec.latest_at_or_before(spec, T0 + timedelta(hours=2), T0) == (
        T0 + timedelta(hours=2)
    )
    assert schedule_spec.latest_at_or_before(spec, T0 - timedelta(seconds=1), T0) is None


def test_cron_uses_timezone_and_dst() -> None:
    spec = ScheduleSpec(kind="Cron", expression="30 2 * * *", timezone="Europe/Paris")
    start = datetime(2027, 3, 27, 12, tzinfo=timezone.utc)
    first = schedule_spec.next_occurrences(spec, start, 1, start)[0]
    # 02:30 does not exist on 2027-03-28 in Paris: fires at the next valid time.
    assert first.isoformat() == "2027-03-28T03:00:00+02:00"
    monday = ScheduleSpec(kind="Cron", expression="0 9 * * MON", timezone="Europe/Paris")
    at = datetime(2026, 10, 5, 7, 0, tzinfo=timezone.utc)  # 09:00 Paris
    assert schedule_spec.latest_at_or_before(monday, at, at) == at


@pytest.mark.parametrize("spec", [
    ScheduleSpec(kind="Interval", every="PT1M"),
    ScheduleSpec(kind="Interval", every="1 hour"),
    ScheduleSpec(kind="Cron", expression="0 9 * * MON"),
    ScheduleSpec(kind="Cron", expression="0 9 * *", timezone="UTC"),
    ScheduleSpec(kind="Cron", expression="0 9 * * MON", timezone="Mars/Olympus"),
    ScheduleSpec(kind="Once", at="2026-11-02T08:00:00"),
])
def test_invalid_specs(spec: ScheduleSpec) -> None:
    with pytest.raises(SpecError):
        schedule_spec.validate(spec)


# -- firing algorithm ------------------------------------------------------------
def test_occurrence_creates_and_starts_a_story(env) -> None:
    cc, svc, clock, _ = env
    schedule = _hourly(svc)
    due = clock.advance(hours=1)
    svc.on_occurrence_due(schedule.id, due, due)

    [run] = _runs(svc, schedule.id)
    assert run.status == ScheduleRunStatus.STARTED
    story = cc.store.stories[run.story_id]
    assert story.schedule_id == schedule.id
    assert story.template_input == {"topic": "risk"}
    assert story.title == "Hourly digest · 2026-10-05"
    execution = cc.store.executions[cc.store.execution_by_story[story.id]]
    assert execution.status == StoryExecutionStatus.RUNNING
    assert any(e.type == "Scheduled Run" for e in cc.store.timelines[execution.id])

    # Duplicate tick for the same occurrence is a no-op.
    svc.on_occurrence_due(schedule.id, due, due)
    assert len(_runs(svc, schedule.id)) == 1


def test_skip_when_previous_run_active(env) -> None:
    _, svc, clock, _ = env
    schedule = _hourly(svc)
    for _ in range(2):
        due = clock.advance(hours=1)
        svc.on_occurrence_due(schedule.id, due, due)
    first, second = _runs(svc, schedule.id)
    assert first.status == ScheduleRunStatus.STARTED
    assert (second.status, second.reason) == (ScheduleRunStatus.SKIPPED, "PreviousRunActive")


def test_buffer_one_keeps_newest_and_releases_after_completion(env) -> None:
    cc, svc, clock, _ = env
    schedule = _hourly(svc, overlap_policy=OverlapPolicy.BUFFER_ONE)
    for _ in range(3):
        due = clock.advance(hours=1)
        svc.on_occurrence_due(schedule.id, due, due)
    first, replaced, buffered = _runs(svc, schedule.id)
    assert (replaced.status, replaced.reason) == (ScheduleRunStatus.SKIPPED, "ReplacedByNewer")
    assert buffered.status == ScheduleRunStatus.BUFFERED

    svc.reconcile()  # previous still running: stays buffered
    assert svc.runs(schedule.id)[0].status == ScheduleRunStatus.BUFFERED
    _finish(cc, first.story_id, StoryExecutionStatus.COMPLETED)
    svc.reconcile()
    released = next(r for r in svc.runs(schedule.id) if r.id == buffered.id)
    assert released.status == ScheduleRunStatus.STARTED
    assert released.story_id


def test_allow_parallel_starts_every_occurrence(env) -> None:
    _, svc, clock, _ = env
    schedule = _hourly(svc, overlap_policy=OverlapPolicy.ALLOW_PARALLEL)
    for _ in range(2):
        due = clock.advance(hours=1)
        svc.on_occurrence_due(schedule.id, due, due)
    assert [r.status for r in _runs(svc, schedule.id)] == [ScheduleRunStatus.STARTED] * 2


def test_catch_up_window_and_superseded(env) -> None:
    _, svc, clock, _ = env
    schedule = _hourly(svc, catch_up_window="PT2H")
    clock.advance(hours=3, minutes=10)  # occurrences at +1h, +2h, +3h passed
    late = T0 + timedelta(hours=1)
    svc.on_occurrence_due(schedule.id, late, clock())
    latest = T0 + timedelta(hours=3)
    svc.on_occurrence_due(schedule.id, latest - timedelta(hours=1), clock())
    svc.on_occurrence_due(schedule.id, latest, clock())
    outside, superseded, started = _runs(svc, schedule.id)
    assert (outside.status, outside.reason) == (ScheduleRunStatus.MISSED, "OutsideCatchUpWindow")
    assert (superseded.status, superseded.reason) == (ScheduleRunStatus.MISSED, "Superseded")
    assert started.status == ScheduleRunStatus.STARTED


def test_three_failures_auto_pause_and_completed_resets(env) -> None:
    cc, svc, clock, _ = env
    schedule = _hourly(svc, overlap_policy=OverlapPolicy.ALLOW_PARALLEL)

    def fire_and_finish(status: StoryExecutionStatus) -> None:
        due = clock.advance(hours=1)
        svc.on_occurrence_due(schedule.id, due, due)
        _finish(cc, svc.runs(schedule.id)[0].story_id, status)
        svc.reconcile()

    fire_and_finish(StoryExecutionStatus.FAILED)
    fire_and_finish(StoryExecutionStatus.COMPLETED)
    assert cc.store.schedules[schedule.id].consecutive_failures == 0
    for _ in range(3):
        fire_and_finish(StoryExecutionStatus.FAILED)
    paused = cc.store.schedules[schedule.id]
    assert paused.status == ScheduleStatus.PAUSED
    assert paused.pause_reason == SchedulePauseReason.CONSECUTIVE_FAILURES
    assert any(n.type == "SchedulePaused" for n in cc.store.notifications)

    # Paused: the next occurrence is recorded as skipped, not started.
    due = clock.advance(hours=1)
    svc.on_occurrence_due(schedule.id, due, due)
    assert svc.runs(schedule.id)[0].reason == "NotActive"


def test_invalid_template_pauses_schedule(env) -> None:
    cc, svc, clock, _ = env
    schedule = _hourly(svc)
    wd = cc.store.workflow_definitions[WFD]
    cc.store.workflow_definitions[WFD] = wd.model_copy(
        update={"input": {**wd.input, "required": ["topic", "audience"]}}
    )
    due = clock.advance(hours=1)
    svc.on_occurrence_due(schedule.id, due, due)
    [run] = _runs(svc, schedule.id)
    assert (run.status, run.reason) == (ScheduleRunStatus.FAILED_TO_START, "InvalidTemplate")
    assert cc.store.schedules[schedule.id].pause_reason == SchedulePauseReason.INVALID_TEMPLATE
    with pytest.raises(InvariantError):
        svc.resume(schedule.id)  # still invalid


def test_once_completes_and_must_be_future(env) -> None:
    cc, svc, clock, _ = env
    at = T0 + timedelta(days=1)
    schedule = svc.create(
        INITIATIVE, "Kickoff", WFD, {"topic": "x"},
        ScheduleSpec(kind="Once", at=schedule_spec.to_iso(at)),
    ).schedule
    clock.at = at
    svc.on_occurrence_due(schedule.id, at, at)
    assert cc.store.schedules[schedule.id].status == ScheduleStatus.COMPLETED
    with pytest.raises(InvariantError):
        svc.create(
            INITIATIVE, "Past", WFD, {"topic": "x"},
            ScheduleSpec(kind="Once", at="2020-01-01T00:00:00Z"),
        )


def test_auto_archive_keeps_last_completed(env) -> None:
    cc, svc, clock, _ = env
    schedule = _hourly(svc, keep_completed=1, overlap_policy=OverlapPolicy.ALLOW_PARALLEL)
    stories = []
    for _ in range(3):
        due = clock.advance(hours=1)
        svc.on_occurrence_due(schedule.id, due, due)
        stories.append(svc.runs(schedule.id)[0].story_id)
    _finish(cc, stories[0], StoryExecutionStatus.FAILED)
    _finish(cc, stories[1], StoryExecutionStatus.COMPLETED)
    _finish(cc, stories[2], StoryExecutionStatus.COMPLETED)
    svc.reconcile()
    status = {sid: cc.store.stories[sid].status for sid in stories}
    assert status[stories[0]] != PlanningStatus.ARCHIVED  # failed stays visible
    assert status[stories[1]] == PlanningStatus.ARCHIVED
    assert status[stories[2]] != PlanningStatus.ARCHIVED
    board = cc.get_board(INITIATIVE)
    on_board = {c.story.id for cards in board.columns.values() for c in cards}
    assert stories[1] not in on_board and stories[2] in on_board


def test_trigger_bypasses_overlap_and_keeps_next_occurrence(env) -> None:
    cc, svc, clock, _ = env
    schedule = _hourly(svc)
    nxt = cc.store.schedules[schedule.id].next_occurrence_at
    first = svc.trigger(schedule.id)
    clock.advance(seconds=1)
    second = svc.trigger(schedule.id)  # previous still running: still starts
    assert first.status == second.status == ScheduleRunStatus.STARTED
    assert cc.store.schedules[schedule.id].next_occurrence_at == nxt


def test_edit_drops_buffered_run(env) -> None:
    _, svc, clock, _ = env
    schedule = _hourly(svc, overlap_policy=OverlapPolicy.BUFFER_ONE)
    for _ in range(2):
        due = clock.advance(hours=1)
        svc.on_occurrence_due(schedule.id, due, due)
    svc.update(schedule.id, name="Renamed")
    latest = svc.runs(schedule.id)[0]
    assert (latest.status, latest.reason) == (ScheduleRunStatus.SKIPPED, "Edited")


# -- in-process adapter ---------------------------------------------------------
def test_adapter_delivers_latest_due_and_advances(env) -> None:
    cc, svc, clock, adapter = env
    schedule = _hourly(svc)
    assert cc.store.schedules[schedule.id].next_occurrence_at == "2026-10-05T08:00:00.000Z"
    adapter.tick()  # nothing due yet
    assert svc.runs(schedule.id) == []

    clock.advance(hours=2, minutes=5)  # +1h and +2h passed (e.g. after downtime)
    adapter.tick()
    [run] = svc.runs(schedule.id)  # coalesced into the latest occurrence
    assert run.scheduled_for == "2026-10-05T09:00:00.000Z"
    assert cc.store.schedules[schedule.id].next_occurrence_at == "2026-10-05T10:00:00.000Z"

    svc.pause(schedule.id)
    clock.advance(hours=3)
    adapter.tick()
    assert len(svc.runs(schedule.id)) == 1
    svc.resume(schedule.id)  # resumes from now; no catch-up of paused time
    assert cc.store.schedules[schedule.id].next_occurrence_at == "2026-10-05T13:00:00.000Z"


def test_zero_task_story_completes_on_tick(env) -> None:
    cc, svc, _, _ = env
    run = svc.trigger(_hourly(svc).id)
    cc.engine.tick()
    execution = cc.store.executions[cc.store.execution_by_story[run.story_id]]
    assert execution.status == StoryExecutionStatus.COMPLETED


def test_schedules_persist_in_sqlite(env) -> None:
    cc, svc, _, _ = env
    schedule = _hourly(svc)
    svc.trigger(schedule.id)
    db = Database(":memory:")
    db.save(cc.store)
    restored = Store()
    db.load_into(restored)
    assert restored.schedules[schedule.id].spec.every == "PT1H"
    assert len([r for r in restored.schedule_runs.values() if r.schedule_id == schedule.id]) == 1


# -- API -------------------------------------------------------------------------
def test_schedule_api_flow() -> None:
    body = {
        "initiativeId": INITIATIVE, "name": "Weekly risk review",
        "workflowDefinitionId": WFD, "templateInput": {"topic": "risk"},
        "spec": {"kind": "Cron", "expression": "0 9 * * MON", "timezone": "Europe/Paris"},
    }
    with TestClient(create_app()) as client:
        preview = client.post(f"{BASE}/schedules/preview", json=body)
        assert preview.status_code == 200
        assert "Promotion to Staff Engineer" in preview.json()["sentence"]
        assert len(preview.json()["nextOccurrences"]) == 5

        created = client.post(f"{BASE}/schedules", json={**body, "runNow": True})
        assert created.status_code == 201
        view = created.json()
        sid = view["schedule"]["id"]
        assert view["schedule"]["overlapPolicy"] == "Skip"
        assert view["schedule"]["keepCompleted"] == 5
        assert view["lastRun"]["status"] == "Started"

        runs = client.get(f"{BASE}/schedules/{sid}/runs").json()
        story_id = runs[0]["storyId"]
        board = client.get(f"{BASE}/initiatives/{INITIATIVE}/board").json()
        cards = [c for col in board["columns"].values() for c in col]
        card = next(c for c in cards if c["story"]["id"] == story_id)
        assert card["story"]["scheduleId"] == sid

        assert client.post(f"{BASE}/schedules/{sid}/pause").json()["schedule"]["status"] == "Paused"
        assert client.post(f"{BASE}/schedules/{sid}/resume").json()["schedule"]["status"] == "Active"
        patched = client.patch(f"{BASE}/schedules/{sid}", json={"overlapPolicy": "BufferOne"})
        assert patched.json()["schedule"]["overlapPolicy"] == "BufferOne"
        listed = client.get(f"{BASE}/schedules", params={"initiativeId": INITIATIVE}).json()
        assert [v["schedule"]["id"] for v in listed] == [sid]

        # A definition used by a live schedule cannot be deleted.
        assert client.delete(f"{BASE}/workflow-definitions/{WFD}").status_code == 409

        archived = client.post(f"{BASE}/schedules/{sid}/archive").json()
        assert archived["schedule"]["status"] == "Archived"
        assert client.get(f"{BASE}/schedules").json() == []
        assert client.post(f"{BASE}/schedules/{sid}/trigger").status_code == 409


@pytest.mark.parametrize("patch, status", [
    ({"spec": {"kind": "Interval", "every": "PT1M"}}, 422),
    ({"spec": {"kind": "Cron", "expression": "0 9 * * MON"}}, 422),
    ({"templateInput": {}}, 422),
    ({"workflowDefinitionId": "wfd_missing"}, 404),
    ({"initiativeId": "init_missing"}, 404),
])
def test_create_schedule_validation(patch: dict, status: int) -> None:
    body = {
        "initiativeId": INITIATIVE, "name": "Digest", "workflowDefinitionId": WFD,
        "templateInput": {"topic": "x"}, "spec": {"kind": "Interval", "every": "P1D"},
        **patch,
    }
    with TestClient(create_app()) as client:
        resp = client.post(f"{BASE}/schedules", json=body)
        assert resp.status_code == status
        assert resp.headers["content-type"].startswith("application/problem+json")
