"""Application layer: the use-case facade the API depends on. Queries read
projections from the store; commands validate intent and delegate runtime effects
to the WorkflowEngine port. No HTTP or persistence details leak in here."""
from __future__ import annotations

from app.domain.board import column_for, empty_columns
from app.domain.decisions import actions_for
from app.domain.enums import DecisionKind, NotificationStatus, PlanningStatus
from app.domain.events import MessageType
from app.domain.models import (
    Artifact,
    Capability,
    Decision,
    HumanRequest,
    Initiative,
    InitiativeBoardView,
    InitiativeSummary,
    Notification,
    Provider,
    Story,
    StoryCardView,
    StoryDraft,
    StoryExecution,
    Task,
    TimelineEvent,
)
from app.infra.store import Store
from app.workflow.simulation import (
    ExecutionNotFound,
    HumanRequestNotFound,
    SimulationEngine,
)

_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

_BULLET_MARKERS = ("-", "*", "•")


def _draft_from_message(message: str) -> StoryDraft:
    """Heuristic stand-in for an LLM: split a free-text brief into story fields.
    Bullet lines become acceptance criteria; the first sentence becomes a title."""
    text = message.strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets = [ln[1:].strip() for ln in lines if ln[:1] in _BULLET_MARKERS and ln[1:].strip()]
    prose = [ln for ln in lines if ln[:1] not in _BULLET_MARKERS]
    first = prose[0] if prose else (lines[0] if lines else "")
    title = first.split(". ")[0][:80].strip()
    description = "\n".join(prose).strip() or text
    lower = text.lower()
    if any(k in lower for k in ("urgent", "critical", "asap", "high priority")):
        priority = 0
    elif "low priority" in lower or "nice to have" in lower:
        priority = 2
    else:
        priority = 1
    return StoryDraft(
        title=title, description=description, priority=priority,
        acceptance_criteria=bullets,
    )


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvariantError(Exception):
    """A command that violates an aggregate invariant (maps to HTTP 422)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# Open notification states in display order; CLOSED is terminal (excluded).
_NOTIFICATION_ORDER = {
    NotificationStatus.UNREAD: 0,
    NotificationStatus.READ: 1,
    NotificationStatus.ACKED: 2,
}


class ControlCenter:
    def __init__(self, store: Store, engine: SimulationEngine) -> None:
        self.store = store
        self.engine = engine

    # -- queries -----------------------------------------------------------
    def get_initiatives(self) -> list[InitiativeSummary]:
        """Lightweight board-list rows (no columns), sorted by initiative order."""
        summaries: list[InitiativeSummary] = []
        for initiative in sorted(self.store.initiatives.values(), key=lambda i: i.order):
            if initiative.status == PlanningStatus.DELETED:
                continue
            epic = self._epic_for_initiative(initiative.id)
            if not epic:
                continue
            stories = [s for s in self.store.stories.values() if s.epic_id == epic.id]
            open_total = sum(self.store.open_requests_for_story(s.id) for s in stories)
            summaries.append(
                InitiativeSummary(
                    initiative=initiative, epic_id=epic.id,
                    story_count=len(stories), open_human_requests=open_total,
                )
            )
        return summaries

    def get_board(self, initiative_id: str) -> InitiativeBoardView:
        """Full Kanban projection for a single initiative."""
        initiative = self.store.initiatives.get(initiative_id)
        if not initiative or initiative.status == PlanningStatus.DELETED:
            raise NotFoundError(f"Initiative not found: {initiative_id}")
        epic = self._epic_for_initiative(initiative_id)
        if not epic:
            raise NotFoundError(f"Initiative has no epic: {initiative_id}")
        columns = empty_columns()
        open_total = 0
        stories = sorted(
            (s for s in self.store.stories.values() if s.epic_id == epic.id),
            key=lambda s: s.priority,
        )
        for story in stories:
            exec_id = self.store.execution_by_story.get(story.id)
            execution = self.store.executions.get(exec_id) if exec_id else None
            open_reqs = self.store.open_requests_for_story(story.id)
            open_total += open_reqs
            column = column_for(story, execution, open_reqs)
            columns[column].append(
                StoryCardView(
                    story=story, column=column, execution=execution,
                    open_human_requests=open_reqs,
                )
            )
        return InitiativeBoardView(
            initiative=initiative, epic_id=epic.id, columns=columns,
            open_human_requests=open_total,
        )

    def create_initiative(self, title: str, description: str) -> Initiative:
        return self.store.create_initiative(title, description)

    def delete_initiative(self, initiative_id: str) -> list[InitiativeSummary]:
        """Soft-delete an initiative (status -> DELETED) and reparent its stories
        onto the default `Misc` initiative. Returns the refreshed summary list."""
        from app.infra.store import MISC_INITIATIVE_ID

        initiative = self.store.initiatives.get(initiative_id)
        if not initiative or initiative.status == PlanningStatus.DELETED:
            raise NotFoundError(f"Initiative not found: {initiative_id}")
        if initiative_id == MISC_INITIATIVE_ID:
            raise InvariantError("The Misc initiative cannot be deleted")
        self.store.soft_delete_initiative(initiative_id)
        return self.get_initiatives()

    def create_story(
        self, epic_id: str, title: str, description: str = "",
        priority: int = 1, acceptance_criteria: list[str] | None = None,
    ) -> Story:
        if epic_id not in self.store.epics:
            raise NotFoundError(f"Epic not found: {epic_id}")
        return self.store.create_story(
            epic_id, title, description, priority, acceptance_criteria
        )

    def draft_story(self, initiative_id: str, message: str) -> StoryDraft:
        """LLM-assisted prefill for the create-story form. Until an LLM provider
        is wired, this is a deterministic heuristic over the free-text message."""
        if not self._epic_for_initiative(initiative_id):
            raise NotFoundError(f"Initiative not found: {initiative_id}")
        return _draft_from_message(message)

    def reorder_initiatives(self, ids: list[str]) -> list[InitiativeSummary]:
        self.store.reorder_initiatives(ids)
        return self.get_initiatives()

    def _epic_for_initiative(self, initiative_id: str):
        return next(
            (e for e in self.store.epics.values() if e.initiative_id == initiative_id),
            None,
        )

    def get_story_tasks(self, story_id: str) -> list[Task]:
        return self.engine._story_tasks(story_id)

    def get_execution(self, execution_id: str) -> StoryExecution:
        exec = self.store.executions.get(execution_id)
        if not exec:
            raise NotFoundError(f"Execution not found: {execution_id}")
        return exec

    def get_timeline(self, execution_id: str) -> list[TimelineEvent]:
        return list(reversed(self.store.timelines.get(execution_id, [])))

    def get_artifacts(self, story_id: str) -> list[Artifact]:
        return list(self.store.artifacts_by_story.get(story_id, []))

    def get_artifact(self, artifact_id: str) -> Artifact:
        for artifacts in self.store.artifacts_by_story.values():
            for a in artifacts:
                if a.id == artifact_id:
                    return a
        raise NotFoundError(f"Artifact not found: {artifact_id}")

    def get_attention(self) -> list[HumanRequest]:
        open_requests = [
            self._with_actions(r) for r in self.store.human_requests.values()
            if r.status not in ("Closed", "Resolved")
        ]
        return sorted(
            open_requests,
            key=lambda r: (_PRIORITY_RANK.get(str(r.priority), 1), r.created_at),
        )

    def get_open_decisions(self, execution_id: str) -> list[HumanRequest]:
        """Open decisions-to-make for an execution, each carrying its action enum."""
        return [
            self._with_actions(r) for r in self.store.human_requests.values()
            if r.execution_id == execution_id and r.status not in ("Closed", "Resolved")
        ]

    def get_decision_history(self, execution_id: str) -> list[Decision]:
        """Recorded, immutable decisions (audit trail) for an execution."""
        req_ids = {
            r.id for r in self.store.human_requests.values()
            if r.execution_id == execution_id
        }
        return [d for d in self.store.decisions.values() if d.human_request_id in req_ids]

    @staticmethod
    def _with_actions(request: HumanRequest) -> HumanRequest:
        return request.model_copy(update={"actions": actions_for(request.type)})

    def get_capabilities(self) -> list[Capability]:
        return list(self.store.capabilities.values())

    def get_providers(self) -> list[Provider]:
        return list(self.store.providers.values())

    def get_notifications(self) -> list[Notification]:
        """Open notifications only (excludes CLOSED), ordered by status
        (UNREAD, READ, ACKED) then ascending by time."""
        open_notifications = [
            n for n in self.store.notifications
            if n.status != NotificationStatus.CLOSED
        ]
        return sorted(
            open_notifications,
            key=lambda n: (_NOTIFICATION_ORDER[n.status], n.created_at),
        )

    # -- commands ----------------------------------------------------------
    def mark_task_ready(self, task_id: str) -> None:
        self.engine.mark_task_ready(task_id)

    def start_story(self, story_id: str) -> StoryExecution:
        try:
            return self.engine.start_story(story_id)
        except ExecutionNotFound as e:
            raise NotFoundError(f"Story not found: {e}") from e

    def start_task(self, task_id: str) -> None:
        self.engine.start_task(task_id)

    def cancel_execution(self, execution_id: str) -> None:
        self.engine.cancel(execution_id)

    def retry_execution(self, execution_id: str) -> None:
        self.engine.retry(execution_id)

    def submit_decision(
        self, human_request_id: str, decision: DecisionKind,
        comment: str | None = None, selected_option: str | None = None,
        action_name: str | None = None,
    ) -> Decision:
        try:
            return self.engine.apply_decision(
                human_request_id, decision, comment=comment,
                selected_option=selected_option, action_name=action_name,
            )
        except HumanRequestNotFound as e:
            raise NotFoundError(f"Human request not found: {e}") from e

    def open_notification(self, notification_id: str) -> None:
        self._transition_notification(
            notification_id, NotificationStatus.UNREAD, NotificationStatus.READ
        )

    def ack_notification(self, notification_id: str) -> None:
        self._transition_notification(
            notification_id, NotificationStatus.READ, NotificationStatus.ACKED
        )

    def close_notification(self, notification_id: str) -> None:
        self._transition_notification(
            notification_id, NotificationStatus.ACKED, NotificationStatus.CLOSED
        )

    def _transition_notification(
        self, notification_id: str,
        expected: NotificationStatus, target: NotificationStatus,
    ) -> None:
        n = next((x for x in self.store.notifications if x.id == notification_id), None)
        if not n:
            raise NotFoundError(f"Notification not found: {notification_id}")
        if n.status != expected:
            raise InvariantError(
                f"Notification {notification_id} is {n.status}; "
                f"{target} requires {expected}"
            )
        n.status = target
        self.store.bus.emit(MessageType.NOTIFICATION_CREATED, n.id, {"status": str(target)})


def build_control_center() -> ControlCenter:
    """Compose the object graph (store + engine + service), restore persisted
    state from SQLite (or seed on first run), and wire write-through persistence:
    every state change signalled on the event bus flushes the store to SQLite."""
    from app.config import settings
    from app.infra.db import Database
    from app.infra.seed import seed

    store = Store()
    engine = SimulationEngine(store)

    db = Database(settings.sqlite_path)
    store.db = db
    if db.has_data():
        db.load_into(store)
    else:
        seed(store, engine)
        db.save(store)

    # Persist on every state change. Subscribed after seed so the initial load
    # is a single write, not one per seeded aggregate.
    store.bus.subscribe(lambda _message: db.save(store))

    return ControlCenter(store, engine)
