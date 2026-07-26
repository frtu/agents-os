"""In-memory persistence + event bus. This is the MVP adapter behind the
repository/event-bus seam; a Postgres-backed store slots in here later without
touching the application or domain layers."""
from __future__ import annotations

import itertools
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.domain.events import MessageType, RealtimeMessage
from app.domain.models import (
    Artifact,
    Capability,
    Decision,
    HumanRequest,
    Initiative,
    Notification,
    Provider,
    Story,
    StoryExecution,
    Task,
    TimelineEvent,
)

_counter = itertools.count(1)


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def now(offset_ms: int = 0) -> str:
    """ISO-8601 UTC timestamp with a trailing Z, matching the frontend mock."""
    dt = datetime.now(timezone.utc) + timedelta(milliseconds=offset_ms)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class EpicRow:
    __slots__ = ("id", "initiative_id", "title")

    def __init__(self, id: str, initiative_id: str, title: str) -> None:
        self.id = id
        self.initiative_id = initiative_id
        self.title = title


class EventBus:
    """Synchronous fan-out. Subscribers (WebSocket connections) receive every
    message; the sequence is monotonic and global (sufficient for the client,
    which uses messages only to invalidate cached queries)."""

    def __init__(self) -> None:
        self._subscribers: set[Callable[[RealtimeMessage], None]] = set()
        self._seq = itertools.count(1)

    def subscribe(self, callback: Callable[[RealtimeMessage], None]) -> Callable[[], None]:
        self._subscribers.add(callback)

        def unsubscribe() -> None:
            self._subscribers.discard(callback)

        return unsubscribe

    def emit(
        self, type: MessageType, aggregate_id: str, payload: dict | None = None
    ) -> None:
        msg = RealtimeMessage(
            type=type,
            aggregate_id=aggregate_id,
            sequence=next(self._seq),
            payload=payload,
        )
        for callback in list(self._subscribers):
            callback(msg)


class Store:
    """Holds every aggregate + projection in memory."""

    def __init__(self) -> None:
        self.initiatives: dict[str, Initiative] = {}
        self.epics: dict[str, EpicRow] = {}
        self.stories: dict[str, Story] = {}
        self.tasks: dict[str, Task] = {}
        self.capabilities: dict[str, Capability] = {}
        self.providers: dict[str, Provider] = {}
        self.executions: dict[str, StoryExecution] = {}
        self.execution_by_story: dict[str, str] = {}
        self.human_requests: dict[str, HumanRequest] = {}
        self.decisions: dict[str, Decision] = {}
        self.artifacts_by_story: dict[str, list[Artifact]] = {}
        self.timelines: dict[str, list[TimelineEvent]] = {}
        self.notifications: list[Notification] = []
        self.bus = EventBus()
        self.seeded = False

    # -- projections helpers used across layers ---------------------------
    def add_timeline(
        self, execution_id: str, type: str, category, detail: str | None = None
    ) -> None:
        entry = TimelineEvent(
            id=uid("tl"),
            execution_id=execution_id,
            type=type,
            category=category,
            detail=detail,
            occurred_at=now(),
        )
        self.timelines.setdefault(execution_id, []).append(entry)
        self.bus.emit(MessageType.TIMELINE_UPDATED, execution_id)

    def push_notification(self, type: str, message: str) -> None:
        n = Notification(
            id=uid("ntf"), type=type, message=message, read=False, created_at=now()
        )
        self.notifications.insert(0, n)
        self.bus.emit(MessageType.NOTIFICATION_CREATED, n.id, {"message": message})

    def open_requests_for_story(self, story_id: str) -> int:
        return sum(
            1
            for r in self.human_requests.values()
            if r.story_id == story_id and r.status not in ("Closed", "Resolved")
        )

    def initiative_for_story(self, story_id: str) -> Initiative | None:
        story = self.stories.get(story_id)
        if not story:
            return None
        epic = self.epics.get(story.epic_id)
        if not epic:
            return None
        return self.initiatives.get(epic.initiative_id)
