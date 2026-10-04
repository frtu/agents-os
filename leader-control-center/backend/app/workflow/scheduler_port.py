"""SchedulerPort (specs/workflow-engine/workflow-engine.md#scheduler-port-time-triggers).
Adapters are clocks only: they call the bound callback with
(schedule_id, scheduled_for, fired_at) when an occurrence is due, and the
application decides overlap and catch-up. Engine schedule ids and policies never
appear in this contract."""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Protocol

from app.domain.models import Schedule

OccurrenceCallback = Callable[[str, datetime, datetime], None]


class SchedulerPort(Protocol):
    def bind(self, callback: OccurrenceCallback) -> None:
        """Set the application callback invoked for each due occurrence."""

    def register(self, schedule: Schedule) -> None:
        """Create or replace the timer for a Schedule (next occurrence from now)."""

    def pause(self, schedule_id: str) -> None:
        """Stop delivering occurrences for a Schedule."""

    def resume(self, schedule: Schedule) -> None:
        """Resume from now; occurrences that passed while paused are not caught up."""

    def remove(self, schedule_id: str) -> None:
        """Delete the timer for a Schedule."""
