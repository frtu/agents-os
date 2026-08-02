"""In-memory working set + event bus. Aggregates live in these dicts at runtime;
durability is provided by the SQLite `Database` (app/infra/db.py) wired in as a
write-through behind the event bus, so the application and domain layers are
untouched. A Postgres/normalized store can replace the seam later the same way."""
from __future__ import annotations

import itertools
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from app.infra.db import Database

from app.domain.enums import NotificationStatus, PlanningStatus
from app.domain.events import MessageType, RealtimeMessage
from app.domain.models import (
    AcceptanceCriteria,
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
    WorkflowDefinition,
)

_counter = itertools.count(1)

# Stable id of the default initiative that hosts stories orphaned by a deletion.
MISC_INITIATIVE_ID = "init_misc"


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
        self.workflow_definitions: dict[str, WorkflowDefinition] = {}
        self.executions: dict[str, StoryExecution] = {}
        self.execution_by_story: dict[str, str] = {}
        self.human_requests: dict[str, HumanRequest] = {}
        self.decisions: dict[str, Decision] = {}
        self.artifacts_by_story: dict[str, list[Artifact]] = {}
        self.timelines: dict[str, list[TimelineEvent]] = {}
        self.notifications: list[Notification] = []
        self.bus = EventBus()
        self.seeded = False
        self.db: "Database | None" = None  # set by build_control_center

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
            id=uid("ntf"), type=type, message=message,
            status=NotificationStatus.UNREAD, created_at=now(),
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

    # -- initiative commands ----------------------------------------------
    def create_initiative(
        self, title: str, description: str,
        workflow_definition_id: str | None = None,
    ) -> Initiative:
        """Create an initiative plus its backing epic (a board needs an epic)."""
        init_id = uid("init")
        initiative = Initiative(
            id=init_id, portfolio_id="portfolio_default",
            title=title, description=description, status="Draft",
            order=len(self.initiatives),
            workflow_definition_id=workflow_definition_id,
            created_at=now(), updated_at=now(),
        )
        self.initiatives[init_id] = initiative
        epic_id = f"epic_{init_id}"
        self.epics[epic_id] = EpicRow(epic_id, init_id, title)
        self.bus.emit(MessageType.STORY_UPDATED, init_id)
        return initiative

    def update_initiative(
        self, initiative_id: str, title: str, description: str,
        workflow_definition_id: str | None = None,
    ) -> Initiative:
        """Update an initiative's editable planning fields, keeping its backing
        epic title in sync. Bumps version; leaves runtime aggregates untouched."""
        existing = self.initiatives[initiative_id]
        updated = existing.model_copy(update={
            "title": title,
            "description": description,
            "workflow_definition_id": workflow_definition_id,
            "version": existing.version + 1,
            "updated_at": now(),
        })
        self.initiatives[initiative_id] = updated
        for epic in self.epics.values():
            if epic.initiative_id == initiative_id:
                epic.title = title
        self.bus.emit(MessageType.STORY_UPDATED, initiative_id)
        return updated

    def ensure_misc_initiative(self) -> Initiative:
        """The `Misc` initiative is created lazily the first time a deletion
        orphans a story, so it never clutters a fresh install."""
        misc = self.initiatives.get(MISC_INITIATIVE_ID)
        if misc:
            return misc
        misc = Initiative(
            id=MISC_INITIATIVE_ID, portfolio_id="portfolio_default",
            title="Misc", description="Stories without a parent initiative.",
            status="Ready", order=len(self.initiatives),
            created_at=now(), updated_at=now(),
        )
        self.initiatives[MISC_INITIATIVE_ID] = misc
        epic_id = f"epic_{MISC_INITIATIVE_ID}"
        self.epics[epic_id] = EpicRow(epic_id, MISC_INITIATIVE_ID, "Misc")
        return misc

    def soft_delete_initiative(self, initiative_id: str) -> None:
        """Mark an initiative DELETED and reparent its stories onto Misc so no
        planning work is lost. Runtime aggregates are left untouched."""
        initiative = self.initiatives[initiative_id]
        epic_ids = {e.id for e in self.epics.values() if e.initiative_id == initiative_id}
        orphans = [s for s in self.stories.values() if s.epic_id in epic_ids]
        if orphans:
            misc = self.ensure_misc_initiative()
            misc_epic = next(
                e.id for e in self.epics.values() if e.initiative_id == misc.id
            )
            for story in orphans:
                self.stories[story.id] = story.model_copy(
                    update={"epic_id": misc_epic, "updated_at": now()}
                )
        self.initiatives[initiative_id] = initiative.model_copy(
            update={"status": PlanningStatus.DELETED, "updated_at": now()}
        )
        self.bus.emit(MessageType.STORY_UPDATED, initiative_id)

    def reorder_initiatives(self, ids: list[str]) -> None:
        """Assign order = position for each known id (unlisted ones keep theirs)."""
        for index, init_id in enumerate(ids):
            initiative = self.initiatives.get(init_id)
            if initiative:
                self.initiatives[init_id] = initiative.model_copy(
                    update={"order": index, "updated_at": now()}
                )
        self.bus.emit(MessageType.STORY_UPDATED, "initiatives")

    # -- story commands ---------------------------------------------------
    def create_story(
        self, epic_id: str, title: str, description: str = "",
        priority: int = 1, acceptance_criteria: list[str] | None = None,
        workflow_definition_id: str | None = None,
        template_input: dict | None = None,
    ) -> Story:
        """Create a Draft story on an epic (lands in the Todo column)."""
        story_id = uid("story")
        story = Story(
            id=story_id, epic_id=epic_id, title=title, description=description,
            priority=priority, status="Draft",
            acceptance_criteria=[
                AcceptanceCriteria(id=uid("ac"), description=d)
                for d in (acceptance_criteria or [])
                if d.strip()
            ],
            workflow_definition_id=workflow_definition_id,
            template_input=template_input,
            created_at=now(), updated_at=now(),
        )
        self.stories[story_id] = story
        self.bus.emit(MessageType.STORY_UPDATED, story_id)
        return story

    def update_story(
        self, story_id: str, title: str, description: str,
        priority: int, acceptance_criteria: list[str] | None = None,
    ) -> Story:
        """Update a story's editable planning fields. Acceptance criteria are
        replaced wholesale (re-issued fresh ids). Bumps version."""
        existing = self.stories[story_id]
        updated = existing.model_copy(update={
            "title": title,
            "description": description,
            "priority": priority,
            "acceptance_criteria": [
                AcceptanceCriteria(id=uid("ac"), description=d)
                for d in (acceptance_criteria or [])
                if d.strip()
            ],
            "version": existing.version + 1,
            "updated_at": now(),
        })
        self.stories[story_id] = updated
        self.bus.emit(MessageType.STORY_UPDATED, story_id)
        return updated

    def soft_delete_story(self, story_id: str) -> None:
        """Mark a story DELETED so it drops out of every board projection.
        Runtime aggregates (executions/history) are left untouched."""
        existing = self.stories[story_id]
        self.stories[story_id] = existing.model_copy(
            update={"status": PlanningStatus.DELETED, "updated_at": now()}
        )
        self.bus.emit(MessageType.STORY_UPDATED, story_id)

    # -- workflow-definition commands -------------------------------------
    def create_workflow_definition(
        self, name: str, input: dict, definition: str,
    ) -> WorkflowDefinition:
        wd_id = uid("wfd")
        wd = WorkflowDefinition(
            id=wd_id, portfolio_id="portfolio_default",
            name=name, input=input, definition=definition,
            created_at=now(), updated_at=now(),
        )
        self.workflow_definitions[wd_id] = wd
        self.bus.emit(MessageType.WORKFLOW_DEFINITION_UPDATED, wd_id)
        return wd

    def update_workflow_definition(
        self, wd_id: str,
        name: str | None = None, input: dict | None = None,
        definition: str | None = None,
    ) -> WorkflowDefinition:
        existing = self.workflow_definitions[wd_id]
        updates: dict = {"updated_at": now(), "version": existing.version + 1}
        if name is not None:
            updates["name"] = name
        if input is not None:
            updates["input"] = input
        if definition is not None:
            updates["definition"] = definition
        updated = existing.model_copy(update=updates)
        self.workflow_definitions[wd_id] = updated
        self.bus.emit(MessageType.WORKFLOW_DEFINITION_UPDATED, wd_id)
        return updated

    def delete_workflow_definition(self, wd_id: str) -> None:
        del self.workflow_definitions[wd_id]
        self.bus.emit(MessageType.WORKFLOW_DEFINITION_UPDATED, wd_id)
