"""In-process SchedulerPort adapter (default; works with the SimulationEngine).
The cursor is the Schedule's `next_occurrence_at`, persisted with the store, so
restarts keep their place. `tick()` is driven by an asyncio loop in the app
lifespan; on each tick it delivers the latest due occurrence per Schedule.
Older missed occurrences are coalesced into that one delivery (OpenClaw-style),
and the application applies the catch-up window to it."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from app.domain import schedule_spec
from app.domain.enums import ScheduleStatus
from app.domain.models import Schedule
from app.infra.store import Store
from app.workflow.scheduler_port import OccurrenceCallback


class InProcessScheduler:
    def __init__(self, store: Store, clock: Callable[[], datetime]) -> None:
        self.store = store
        self.clock = clock
        self._callback: OccurrenceCallback | None = None

    def bind(self, callback: OccurrenceCallback) -> None:
        self._callback = callback

    def register(self, schedule: Schedule) -> None:
        self._set_cursor(schedule.id, self._next_after(schedule, self.clock()))

    def pause(self, schedule_id: str) -> None:
        self._set_cursor(schedule_id, None)

    def resume(self, schedule: Schedule) -> None:
        self.register(schedule)

    def remove(self, schedule_id: str) -> None:
        self._set_cursor(schedule_id, None)

    def tick(self) -> None:
        now = self.clock()
        for schedule in list(self.store.schedules.values()):
            if schedule.status != ScheduleStatus.ACTIVE or not schedule.next_occurrence_at:
                continue
            if schedule_spec.parse_instant(schedule.next_occurrence_at) > now:
                continue
            anchor = schedule_spec.parse_instant(schedule.created_at)
            latest = schedule_spec.latest_at_or_before(schedule.spec, now, anchor)
            # Advance first: a failing callback must not re-deliver forever.
            self._set_cursor(schedule.id, self._next_after(schedule, now))
            if latest is not None and self._callback is not None:
                self._callback(schedule.id, latest, now)

    def _next_after(self, schedule: Schedule, instant: datetime) -> str | None:
        anchor = schedule_spec.parse_instant(schedule.created_at)
        upcoming = schedule_spec.next_occurrences(schedule.spec, instant, 1, anchor)
        return schedule_spec.to_iso(upcoming[0]) if upcoming else None

    def _set_cursor(self, schedule_id: str, value: str | None) -> None:
        schedule = self.store.schedules.get(schedule_id)
        if schedule is not None and schedule.next_occurrence_at != value:
            self.store.put_schedule(schedule.model_copy(update={"next_occurrence_at": value}))
