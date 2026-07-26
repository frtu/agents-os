"""Application layer: the use-case facade the API depends on. Queries read
projections from the store; commands validate intent and delegate runtime effects
to the WorkflowEngine port. No HTTP or persistence details leak in here."""
from __future__ import annotations

from app.domain.board import column_for, empty_columns
from app.domain.enums import DecisionKind
from app.domain.models import (
    Artifact,
    Capability,
    Decision,
    HumanRequest,
    InitiativeBoardView,
    Notification,
    Provider,
    StoryCardView,
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


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ControlCenter:
    def __init__(self, store: Store, engine: SimulationEngine) -> None:
        self.store = store
        self.engine = engine

    # -- queries -----------------------------------------------------------
    def get_boards(self) -> list[InitiativeBoardView]:
        views: list[InitiativeBoardView] = []
        for initiative in self.store.initiatives.values():
            epic = next(
                (e for e in self.store.epics.values() if e.initiative_id == initiative.id),
                None,
            )
            if not epic:
                continue
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
            views.append(
                InitiativeBoardView(
                    initiative=initiative, epic_id=epic.id, columns=columns,
                    open_human_requests=open_total,
                )
            )
        return views

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
            r for r in self.store.human_requests.values()
            if r.status not in ("Closed", "Resolved")
        ]
        return sorted(
            open_requests,
            key=lambda r: (_PRIORITY_RANK.get(str(r.priority), 1), r.created_at),
        )

    def get_decisions(self, execution_id: str) -> list[Decision]:
        req_ids = {
            r.id for r in self.store.human_requests.values()
            if r.execution_id == execution_id
        }
        return [d for d in self.store.decisions.values() if d.human_request_id in req_ids]

    def get_capabilities(self) -> list[Capability]:
        return list(self.store.capabilities.values())

    def get_providers(self) -> list[Provider]:
        return list(self.store.providers.values())

    def get_notifications(self) -> list[Notification]:
        return list(self.store.notifications)

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
    ) -> Decision:
        try:
            return self.engine.apply_decision(
                human_request_id, decision, comment=comment, selected_option=selected_option
            )
        except HumanRequestNotFound as e:
            raise NotFoundError(f"Human request not found: {e}") from e

    def dismiss_notification(self, notification_id: str) -> None:
        self.engine.dismiss_notification(notification_id)


def build_control_center() -> ControlCenter:
    """Compose the object graph (store + engine + service) and seed it."""
    from app.infra.seed import seed

    store = Store()
    engine = SimulationEngine(store)
    seed(store, engine)
    return ControlCenter(store, engine)
