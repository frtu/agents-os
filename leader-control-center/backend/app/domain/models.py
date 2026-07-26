"""Domain models. These are the projections the API returns; field names
serialize to camelCase so the JSON matches the frontend contract exactly
(frontend/src/types/domain.ts). The domain layer has no FastAPI/HTTP imports."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.domain.enums import (
    ArtifactType,
    BoardColumn,
    CapabilityExecutionStatus,
    DecisionKind,
    ExecutionStrategy,
    HumanRequestStatus,
    HumanRequestType,
    PlanningMode,
    PlanningStatus,
    Priority,
    ProviderExecutionStatus,
    ProviderType,
    TaskExecutionStatus,
    TaskPlanningStatus,
    StoryExecutionStatus,
    TimelineEventCategory,
)


class Schema(BaseModel):
    """Base model: snake_case in Python, camelCase on the wire."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Resource(Schema):
    id: str
    version: int = 1
    created_at: str
    updated_at: str


# --- Planning -------------------------------------------------------------
class Initiative(Resource):
    portfolio_id: str
    title: str
    description: str
    status: PlanningStatus


class AcceptanceCriteria(Schema):
    id: str
    description: str


class Story(Resource):
    epic_id: str
    title: str
    description: str
    priority: int
    status: PlanningStatus
    acceptance_criteria: list[AcceptanceCriteria] = []


class Task(Resource):
    story_id: str
    name: str
    planning_mode: PlanningMode
    status: TaskPlanningStatus
    order: int
    dependencies: list[str] = []
    capability_id: str | None = None
    goal: str | None = None
    success_criteria: list[str] | None = None


# --- Catalog --------------------------------------------------------------
class Capability(Schema):
    id: str
    name: str
    description: str
    inputs: str
    outputs: str
    supported_providers: list[str]


class Provider(Schema):
    id: str
    name: str
    type: ProviderType


# --- Runtime --------------------------------------------------------------
class ProviderExecution(Schema):
    id: str
    capability_execution_id: str
    provider_id: str
    provider_name: str
    status: ProviderExecutionStatus
    attempt: int
    started_at: str | None = None
    ended_at: str | None = None


class CapabilityExecution(Schema):
    id: str
    task_execution_id: str
    capability_id: str
    capability_name: str
    strategy: ExecutionStrategy
    status: CapabilityExecutionStatus
    provider_executions: list[ProviderExecution] = []


class TaskExecution(Schema):
    id: str
    story_execution_id: str
    task_id: str
    task_name: str
    status: TaskExecutionStatus
    attempt: int
    waiting_reason: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    capability_executions: list[CapabilityExecution] = []


class StoryExecution(Schema):
    id: str
    story_id: str
    status: StoryExecutionStatus
    progress: float
    started_at: str | None = None
    completed_at: str | None = None
    task_executions: list[TaskExecution] = []


# --- Human interaction ----------------------------------------------------
class HumanRequestOption(Schema):
    id: str
    label: str


class HumanRequest(Schema):
    id: str
    execution_id: str
    initiative_id: str
    initiative_title: str
    story_id: str
    story_title: str
    type: HumanRequestType
    prompt: str
    options: list[HumanRequestOption] | None = None
    status: HumanRequestStatus
    priority: Priority
    created_at: str


class Decision(Schema):
    id: str
    human_request_id: str
    decision: DecisionKind
    selected_option: str | None = None
    comment: str | None = None
    user: str
    created_at: str


# --- Artifacts & Timeline -------------------------------------------------
class Artifact(Schema):
    id: str
    execution_id: str
    story_id: str
    type: ArtifactType
    name: str
    version: int
    created_by: str
    created_at: str
    parent_artifact_id: str | None = None
    content: str | None = None
    language: str | None = None


class TimelineEvent(Schema):
    id: str
    execution_id: str
    type: str
    category: TimelineEventCategory
    detail: str | None = None
    occurred_at: str


# --- Notifications --------------------------------------------------------
class Notification(Schema):
    id: str
    type: str
    message: str
    read: bool
    created_at: str


# --- Board projection -----------------------------------------------------
class StoryCardView(Schema):
    story: Story
    column: BoardColumn
    execution: StoryExecution | None = None
    open_human_requests: int


class InitiativeBoardView(Schema):
    initiative: Initiative
    epic_id: str
    columns: dict[BoardColumn, list[StoryCardView]]
    open_human_requests: int
