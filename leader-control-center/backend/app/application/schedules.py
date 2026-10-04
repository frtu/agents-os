"""ScheduleService: Schedule commands/queries plus the process manager that turns
due occurrences into Stories (specs/planning/schedules.md). The Schedule
aggregate holds Planning ids only; the runtime-aware rules (overlap, buffered
release, failure counting, auto-archive) live here and read Runtime projections."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Callable

from app.application.errors import ConflictError, InvariantError, NotFoundError
from app.domain import schedule_spec
from app.domain.enums import (
    OverlapPolicy,
    PlanningStatus,
    SchedulePauseReason,
    ScheduleRunStatus,
    ScheduleSpecKind,
    ScheduleStatus,
    StoryExecutionStatus,
    TimelineEventCategory,
)
from app.domain.models import (
    Schedule,
    SchedulePreview,
    ScheduleRun,
    ScheduleSpec,
    ScheduleView,
    StoryExecution,
)
from app.domain.schedule_spec import SpecError, to_iso
from app.infra.store import now, uid
from app.workflow.scheduler_port import SchedulerPort

if TYPE_CHECKING:
    from app.application.service import ControlCenter

FAILURE_LIMIT = 3
ACTOR = "system:scheduler"
_ACTIVE = (
    StoryExecutionStatus.CREATED,
    StoryExecutionStatus.RUNNING,
    StoryExecutionStatus.WAITING,
)
_TERMINAL = (
    StoryExecutionStatus.COMPLETED,
    StoryExecutionStatus.FAILED,
    StoryExecutionStatus.CANCELLED,
)
_PREVIEW_COUNT = 5
# Placeholder until auth exists; matches the user recorded on Decisions.
_CURRENT_USER = "you@leader"


class ScheduleService:
    def __init__(
        self, cc: "ControlCenter", scheduler: SchedulerPort,
        clock: Callable[[], datetime],
    ) -> None:
        self.cc = cc
        self.store = cc.store
        self.scheduler = scheduler
        self.clock = clock
        scheduler.bind(self.on_occurrence_due)

    # -- queries -----------------------------------------------------------
    def list_schedules(
        self, initiative_id: str | None = None, include_archived: bool = False,
    ) -> list[ScheduleView]:
        schedules = [
            s for s in self.store.schedules.values()
            if (initiative_id is None or s.initiative_id == initiative_id)
            and (include_archived or s.status != ScheduleStatus.ARCHIVED)
        ]
        schedules.sort(key=lambda s: (s.initiative_id, s.name.lower()))
        return [self._view(s) for s in schedules]

    def get(self, schedule_id: str) -> ScheduleView:
        return self._view(self._schedule(schedule_id))

    def runs(self, schedule_id: str) -> list[ScheduleRun]:
        self._schedule(schedule_id)
        runs = [r for r in self.store.schedule_runs.values() if r.schedule_id == schedule_id]
        runs.sort(key=lambda r: (r.fired_at, r.scheduled_for), reverse=True)
        return [self._with_outcome(r) for r in runs]

    def preview(
        self, initiative_id: str, name: str, spec: ScheduleSpec,
        overlap_policy: OverlapPolicy, story_title_template: str,
    ) -> SchedulePreview:
        initiative = self._initiative(initiative_id)
        self._validate_spec(spec)
        moment = self.clock()
        upcoming = schedule_spec.next_occurrences(spec, moment, _PREVIEW_COUNT, moment)
        title = self._title(story_title_template, name, spec, upcoming[0] if upcoming else moment, 1)
        return SchedulePreview(
            sentence=schedule_spec.describe(spec, overlap_policy, title, initiative.title),
            next_occurrences=[to_iso(d) for d in upcoming],
        )

    # -- commands ------------------------------------------------------------
    def create(
        self, initiative_id: str, name: str, workflow_definition_id: str,
        template_input: dict, spec: ScheduleSpec,
        overlap_policy: OverlapPolicy = OverlapPolicy.SKIP,
        catch_up_window: str = "PT1H", keep_completed: int = 5,
        story_title_template: str = "{name} · {date}", run_now: bool = False,
    ) -> ScheduleView:
        self._initiative(initiative_id)
        self._validate(
            name, workflow_definition_id, template_input, spec,
            catch_up_window, keep_completed,
        )
        if spec.kind == ScheduleSpecKind.ONCE and (
            schedule_spec.parse_instant(spec.at or "") <= self.clock()
        ):
            raise InvariantError("A Once schedule must be in the future")
        schedule = self.store.put_schedule(Schedule(
            id=uid("sched"), initiative_id=initiative_id, name=name.strip(),
            workflow_definition_id=workflow_definition_id,
            template_input=template_input, story_title_template=story_title_template,
            spec=spec, overlap_policy=overlap_policy, catch_up_window=catch_up_window,
            keep_completed=keep_completed, created_by=_CURRENT_USER,
            created_at=now(), updated_at=now(),
        ))
        self.scheduler.register(schedule)
        if run_now:
            self.trigger(schedule.id)
        return self.get(schedule.id)

    def update(self, schedule_id: str, **changes) -> ScheduleView:
        schedule = self._schedule(schedule_id)
        if schedule.status in (ScheduleStatus.ARCHIVED, ScheduleStatus.COMPLETED):
            raise ConflictError(f"Schedule is {schedule.status}; create a new one instead")
        fields = {k: v for k, v in changes.items() if v is not None}
        merged = schedule.model_copy(update=fields)
        self._validate(
            merged.name, merged.workflow_definition_id, merged.template_input,
            merged.spec, merged.catch_up_window, merged.keep_completed,
        )
        updated = self._save(merged)
        # An edit is a new scheduling decision: pending buffered runs are dropped.
        self._drop_buffered(schedule_id, "Edited")
        if updated.status == ScheduleStatus.ACTIVE:
            self.scheduler.register(updated)
        return self.get(schedule_id)

    def pause(self, schedule_id: str) -> ScheduleView:
        schedule = self._schedule(schedule_id)
        if schedule.status == ScheduleStatus.ACTIVE:
            self._pause(schedule, SchedulePauseReason.MANUAL)
        elif schedule.status != ScheduleStatus.PAUSED:
            raise ConflictError(f"Cannot pause a {schedule.status} schedule")
        return self.get(schedule_id)

    def resume(self, schedule_id: str) -> ScheduleView:
        schedule = self._schedule(schedule_id)
        if schedule.status == ScheduleStatus.ACTIVE:
            return self.get(schedule_id)
        if schedule.status != ScheduleStatus.PAUSED:
            raise ConflictError(f"Cannot resume a {schedule.status} schedule")
        self._validate_template(schedule.workflow_definition_id, schedule.template_input)
        resumed = self._save(schedule.model_copy(update={
            "status": ScheduleStatus.ACTIVE, "pause_reason": None,
            "consecutive_failures": 0,
        }))
        self.scheduler.resume(resumed)
        return self.get(schedule_id)

    def trigger(self, schedule_id: str) -> ScheduleRun:
        """Run one occurrence now (out-of-band). Explicit human intent, so the
        Overlap Policy and catch-up window do not apply; the next natural
        occurrence is unchanged."""
        schedule = self._schedule(schedule_id)
        if schedule.status == ScheduleStatus.ARCHIVED:
            raise ConflictError("Cannot run an archived schedule")
        moment = self.clock()
        return self._with_outcome(self._start(schedule, to_iso(moment), moment))

    def archive(self, schedule_id: str) -> ScheduleView:
        schedule = self._schedule(schedule_id)
        if schedule.status != ScheduleStatus.ARCHIVED:
            self._save(schedule.model_copy(update={"status": ScheduleStatus.ARCHIVED}))
            self.scheduler.remove(schedule_id)
            self._drop_buffered(schedule_id, "Archived")
        return self.get(schedule_id)

    def archive_for_initiative(self, initiative_id: str) -> None:
        for schedule in list(self.store.schedules.values()):
            if schedule.initiative_id == initiative_id:
                self.archive(schedule.id)

    # -- occurrence handling (SchedulerPort callback) ----------------------
    def on_occurrence_due(
        self, schedule_id: str, scheduled_for: datetime, fired_at: datetime,
    ) -> None:
        schedule = self.store.schedules.get(schedule_id)
        if schedule is None:
            return
        due = to_iso(scheduled_for)
        if self._run_for(schedule_id, due) is not None:
            return  # idempotent: one record per occurrence
        if schedule.status != ScheduleStatus.ACTIVE:
            self._record(schedule_id, due, fired_at, ScheduleRunStatus.SKIPPED, "NotActive")
            return
        initiative = self.store.initiatives.get(schedule.initiative_id)
        if initiative is None or initiative.status == PlanningStatus.DELETED:
            self._record(schedule_id, due, fired_at, ScheduleRunStatus.SKIPPED, "InitiativeDeleted")
            self.archive(schedule_id)
            return
        window = schedule_spec.parse_duration(schedule.catch_up_window)
        anchor = schedule_spec.parse_instant(schedule.created_at)
        latest = schedule_spec.latest_at_or_before(schedule.spec, fired_at, anchor)
        if fired_at - scheduled_for > window:
            self._record(schedule_id, due, fired_at, ScheduleRunStatus.MISSED, "OutsideCatchUpWindow")
        elif latest is not None and latest > scheduled_for:
            self._record(schedule_id, due, fired_at, ScheduleRunStatus.MISSED, "Superseded")
        elif self._active_stories(schedule_id):
            self._overlap(schedule, due, fired_at)
        else:
            self._start(schedule, due, fired_at)
        self._maybe_complete(schedule_id)

    def tick(self) -> None:
        """Drive the in-process adapter (if any), then settle finished runs."""
        adapter_tick = getattr(self.scheduler, "tick", None)
        if adapter_tick is not None:
            adapter_tick()
        self.reconcile()

    def reconcile(self) -> None:
        """React to Runtime: settle finished runs (failure count, auto-archive)
        and release a buffered run once nothing of its Schedule is active."""
        for run in list(self.store.schedule_runs.values()):
            if run.status != ScheduleRunStatus.STARTED or run.settled_at or not run.story_id:
                continue
            execution = self._execution(run.story_id)
            if execution is None or execution.status not in _TERMINAL:
                continue
            self.store.put_schedule_run(run.model_copy(update={"settled_at": now()}))
            schedule = self.store.schedules.get(run.schedule_id)
            if schedule is None:
                continue
            if execution.status == StoryExecutionStatus.COMPLETED:
                if schedule.consecutive_failures:
                    self._save(schedule.model_copy(update={"consecutive_failures": 0}))
                self._auto_archive(schedule.id)
            elif execution.status == StoryExecutionStatus.FAILED:
                story = self.store.stories.get(run.story_id)
                self._count_failure(schedule.id, f"'{story.title if story else run.story_id}' failed")

        for schedule in list(self.store.schedules.values()):
            if schedule.status != ScheduleStatus.ACTIVE or self._active_stories(schedule.id):
                continue
            buffered = self._buffered(schedule.id)
            if buffered:
                self._start(schedule, buffered.scheduled_for, self.clock(), buffered)
                self._maybe_complete(schedule.id)

    # -- internals -----------------------------------------------------------
    def _overlap(self, schedule: Schedule, due: str, fired_at: datetime) -> None:
        if schedule.overlap_policy == OverlapPolicy.SKIP:
            self._record(schedule.id, due, fired_at, ScheduleRunStatus.SKIPPED, "PreviousRunActive")
        elif schedule.overlap_policy == OverlapPolicy.BUFFER_ONE:
            self._drop_buffered(schedule.id, "ReplacedByNewer")
            self._record(schedule.id, due, fired_at, ScheduleRunStatus.BUFFERED, "PreviousRunActive")
        else:
            self._start(schedule, due, fired_at)

    def _start(
        self, schedule: Schedule, due: str, fired_at: datetime,
        buffered: ScheduleRun | None = None,
    ) -> ScheduleRun:
        """Create the Story from the template and start it, recording the run.
        A buffered run is promoted in place so the occurrence keeps one record."""
        try:
            self._validate_template(schedule.workflow_definition_id, schedule.template_input)
        except (InvariantError, NotFoundError) as e:
            run = self._record(
                schedule.id, due, fired_at, ScheduleRunStatus.FAILED_TO_START,
                "InvalidTemplate", error=e.message, existing=buffered,
            )
            self._notify_failure(schedule, e.message)
            current = self.store.schedules[schedule.id]
            if current.status == ScheduleStatus.ACTIVE:
                self._pause(current, SchedulePauseReason.INVALID_TEMPLATE)
            return run
        try:
            epic = self.cc._epic_for_initiative(schedule.initiative_id)
            if epic is None:
                raise NotFoundError(f"Initiative has no epic: {schedule.initiative_id}")
            scheduled_for = schedule_spec.parse_instant(due)
            n = 1 + sum(
                1 for r in self.store.schedule_runs.values()
                if r.schedule_id == schedule.id and r.status == ScheduleRunStatus.STARTED
            )
            story = self.store.create_story(
                epic.id,
                self._title(schedule.story_title_template, schedule.name, schedule.spec, scheduled_for, n),
                f"Created by schedule '{schedule.name}' for the occurrence at {due}.",
                workflow_definition_id=schedule.workflow_definition_id,
                template_input=schedule.template_input,
                schedule_id=schedule.id, scheduled_for=due,
            )
            execution = self.cc.start_story(story.id)
            self.store.add_timeline(
                execution.id, "Scheduled Run", TimelineEventCategory.SYSTEM,
                f"{schedule.name} · occurrence {due} · {ACTOR} on behalf of {schedule.created_by}",
            )
        except Exception as e:  # noqa: BLE001 - any start failure is a failed run
            message = getattr(e, "message", None) or str(e) or type(e).__name__
            run = self._record(
                schedule.id, due, fired_at, ScheduleRunStatus.FAILED_TO_START,
                "StartFailed", error=message, existing=buffered,
            )
            self._count_failure(schedule.id, message)
            return run
        return self._record(
            schedule.id, due, fired_at, ScheduleRunStatus.STARTED,
            story_id=story.id, existing=buffered,
        )

    def _count_failure(self, schedule_id: str, message: str) -> None:
        schedule = self.store.schedules[schedule_id]
        failures = schedule.consecutive_failures + 1
        schedule = self._save(schedule.model_copy(update={"consecutive_failures": failures}))
        self._notify_failure(schedule, message)
        if failures >= FAILURE_LIMIT and schedule.status == ScheduleStatus.ACTIVE:
            self._pause(schedule, SchedulePauseReason.CONSECUTIVE_FAILURES)

    def _notify_failure(self, schedule: Schedule, message: str) -> None:
        self.store.push_notification(
            "ScheduleRunFailed", f"Schedule '{schedule.name}' run failed: {message}"
        )

    def _pause(self, schedule: Schedule, reason: SchedulePauseReason) -> None:
        self._save(schedule.model_copy(update={
            "status": ScheduleStatus.PAUSED, "pause_reason": reason,
        }))
        self.scheduler.pause(schedule.id)
        if reason != SchedulePauseReason.MANUAL:
            self.store.push_notification(
                "SchedulePaused",
                f"Schedule '{schedule.name}' was paused automatically ({reason}). "
                "Fix the cause, then resume it.",
            )

    def _auto_archive(self, schedule_id: str) -> None:
        """Keep the newest `keep_completed` Completed Stories on the board;
        Failed/Cancelled ones stay until a leader handles them."""
        schedule = self.store.schedules[schedule_id]
        completed = []
        for story in self.store.stories.values():
            if story.schedule_id != schedule_id or story.status in (
                PlanningStatus.ARCHIVED, PlanningStatus.DELETED,
            ):
                continue
            execution = self._execution(story.id)
            if execution is not None and execution.status == StoryExecutionStatus.COMPLETED:
                completed.append(story)
        completed.sort(key=lambda s: s.scheduled_for or s.created_at, reverse=True)
        for story in completed[schedule.keep_completed:]:
            self.store.archive_story(story.id)

    def _maybe_complete(self, schedule_id: str) -> None:
        schedule = self.store.schedules.get(schedule_id)
        if (
            schedule is not None
            and schedule.spec.kind == ScheduleSpecKind.ONCE
            and schedule.status == ScheduleStatus.ACTIVE
            and self._buffered(schedule_id) is None
            and schedule_spec.parse_instant(schedule.spec.at or "") <= self.clock()
        ):
            self._save(schedule.model_copy(update={"status": ScheduleStatus.COMPLETED}))
            self.scheduler.remove(schedule_id)

    def _drop_buffered(self, schedule_id: str, reason: str) -> None:
        buffered = self._buffered(schedule_id)
        if buffered is not None:
            self.store.put_schedule_run(buffered.model_copy(update={
                "status": ScheduleRunStatus.SKIPPED, "reason": reason,
            }))

    def _record(
        self, schedule_id: str, due: str, fired_at: datetime,
        status: ScheduleRunStatus, reason: str | None = None,
        story_id: str | None = None, error: str | None = None,
        existing: ScheduleRun | None = None,
    ) -> ScheduleRun:
        fields = {
            "status": status, "reason": reason, "story_id": story_id, "error": error,
            "fired_at": to_iso(fired_at),
        }
        if existing is not None:
            return self.store.put_schedule_run(existing.model_copy(update=fields))
        return self.store.put_schedule_run(ScheduleRun(
            id=uid("srun"), schedule_id=schedule_id, scheduled_for=due, **fields,
        ))

    def _save(self, schedule: Schedule) -> Schedule:
        return self.store.put_schedule(schedule.model_copy(update={
            "version": schedule.version + 1, "updated_at": now(),
        }))

    def _run_for(self, schedule_id: str, due: str) -> ScheduleRun | None:
        return next(
            (r for r in self.store.schedule_runs.values()
             if r.schedule_id == schedule_id and r.scheduled_for == due),
            None,
        )

    def _buffered(self, schedule_id: str) -> ScheduleRun | None:
        return next(
            (r for r in self.store.schedule_runs.values()
             if r.schedule_id == schedule_id and r.status == ScheduleRunStatus.BUFFERED),
            None,
        )

    def _active_stories(self, schedule_id: str) -> list[str]:
        return [
            s.id for s in self.store.stories.values()
            if s.schedule_id == schedule_id
            and (e := self._execution(s.id)) is not None and e.status in _ACTIVE
        ]

    def _execution(self, story_id: str) -> StoryExecution | None:
        exec_id = self.store.execution_by_story.get(story_id)
        return self.store.executions.get(exec_id) if exec_id else None

    def _with_outcome(self, run: ScheduleRun) -> ScheduleRun:
        execution = self._execution(run.story_id) if run.story_id else None
        return run.model_copy(update={"outcome": execution.status if execution else None})

    def _view(self, schedule: Schedule) -> ScheduleView:
        initiative = self.store.initiatives.get(schedule.initiative_id)
        anchor = schedule_spec.parse_instant(schedule.created_at)
        upcoming: list[datetime] = []
        if schedule.status == ScheduleStatus.ACTIVE:
            upcoming = schedule_spec.next_occurrences(
                schedule.spec, self.clock(), _PREVIEW_COUNT, anchor
            )
        sample = upcoming[0] if upcoming else self.clock()
        title = self._title(schedule.story_title_template, schedule.name, schedule.spec, sample, 1)
        runs = [r for r in self.store.schedule_runs.values() if r.schedule_id == schedule.id]
        last = max(runs, key=lambda r: (r.fired_at, r.scheduled_for), default=None)
        return ScheduleView(
            schedule=schedule,
            sentence=schedule_spec.describe(
                schedule.spec, schedule.overlap_policy, title,
                initiative.title if initiative else schedule.initiative_id,
            ),
            next_occurrences=[to_iso(d) for d in upcoming],
            last_run=self._with_outcome(last) if last else None,
        )

    @staticmethod
    def _title(
        template: str, name: str, spec: ScheduleSpec, at: datetime, n: int,
    ) -> str:
        local = at.astimezone(schedule_spec.zone_for(spec))
        return schedule_spec.render_title(template, name, local, n)

    def _schedule(self, schedule_id: str) -> Schedule:
        schedule = self.store.schedules.get(schedule_id)
        if schedule is None:
            raise NotFoundError(f"Schedule not found: {schedule_id}")
        return schedule

    def _initiative(self, initiative_id: str):
        initiative = self.store.initiatives.get(initiative_id)
        if initiative is None or initiative.status == PlanningStatus.DELETED:
            raise NotFoundError(f"Initiative not found: {initiative_id}")
        return initiative

    def _validate(
        self, name: str, workflow_definition_id: str, template_input: dict,
        spec: ScheduleSpec, catch_up_window: str, keep_completed: int,
    ) -> None:
        if not name or not name.strip():
            raise InvariantError("Schedule name is required")
        if keep_completed < 0:
            raise InvariantError("keepCompleted must be 0 or more")
        self._validate_spec(spec)
        try:
            schedule_spec.parse_duration(catch_up_window)
        except SpecError as e:
            raise InvariantError(f"catchUpWindow: {e}") from e
        self._validate_template(workflow_definition_id, template_input)

    @staticmethod
    def _validate_spec(spec: ScheduleSpec) -> None:
        try:
            schedule_spec.validate(spec)
        except SpecError as e:
            raise InvariantError(str(e)) from e

    def _validate_template(self, workflow_definition_id: str, template_input: dict) -> None:
        wd = self.store.workflow_definitions.get(workflow_definition_id)
        if wd is None:
            raise NotFoundError(f"Workflow definition not found: {workflow_definition_id}")
        self.cc._validate_template_input(wd, template_input or {})
