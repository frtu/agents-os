"""Domain models. These are the projections the API returns; field names
serialize to camelCase so the JSON matches the frontend contract exactly
(frontend/src/types/domain.ts). The domain layer has no FastAPI/HTTP imports."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.domain.enums import (
    ActivityKind,
    ArtifactType,
    BoardColumn,
    CapabilityExecutionStatus,
    DecisionKind,
    ExecutionStrategy,
    HumanRequestStatus,
    HumanRequestType,
    NotificationStatus,
    OverlapPolicy,
    PlanningMode,
    PlanningStatus,
    Priority,
    ProviderExecutionStatus,
    ProviderType,
    SchedulePauseReason,
    ScheduleRunStatus,
    ScheduleSpecKind,
    ScheduleStatus,
    TaskExecutionStatus,
    TaskPlanningStatus,
    StoryExecutionStatus,
    TimelineEventCategory,
    WebhookMethod,
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
    order: int = 0
    # Optional blueprint governing stories created under this initiative.
    workflow_definition_id: str | None = None


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
    # Set when the story was authored from a workflow definition template.
    workflow_definition_id: str | None = None
    template_input: dict | None = None
    # Set when the story was created by a Schedule occurrence (planning ids only).
    schedule_id: str | None = None
    scheduled_for: str | None = None


class StoryDraft(Schema):
    """LLM-assisted prefill for the create-story form (not a stored resource)."""

    title: str
    description: str
    priority: int
    acceptance_criteria: list[str] = []


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


class WorkflowDefinition(Resource):
    """Authoring-time blueprint (a DSL) for creating workflow executions. Its
    `input` is a JSON Schema governing the parameters a templated story supplies;
    `definition` is the DSL body. Distinct from the Temporal workflow engine."""

    portfolio_id: str
    name: str
    input: dict = {}
    definition: str = ""


class ActivityDefinition(Resource):
    """Reusable bash/webhook building block a Temporal workflow runs as an
    Activity (UI menu "Tasks"). `input` is a JSON Schema for its parameters."""

    portfolio_id: str
    name: str
    description: str = ""
    kind: ActivityKind
    input: dict = {}
    timeout_seconds: int = 300
    # Bash
    script: str | None = None
    # Webhook
    method: WebhookMethod = WebhookMethod.POST
    url: str | None = None
    headers: dict[str, str] = {}
    content_type: str = "application/json"
    body_template: str | None = None


class RenderedActivity(Schema):
    """Preview of an Activity Definition with parameters applied (no side effects).
    Header secrets stay as ${env:NAME} references."""

    kind: ActivityKind
    script: str | None = None
    method: WebhookMethod | None = None
    url: str | None = None
    headers: dict[str, str] = {}
    body: str | None = None


class WebhookTestResult(Schema):
    request: RenderedActivity
    status: int | None = None
    duration_ms: int
    response_headers: dict[str, str] = {}
    response_body: str | None = None
    error: str | None = None


# --- Schedules (specs/planning/schedules.md) -----------------------------
class ScheduleSpec(Schema):
    """When a Schedule fires. Once: `at`; Interval: `every` (+ `anchor`);
    Cron: `expression` + IANA `timezone`. Durations/instants are ISO 8601."""

    kind: ScheduleSpecKind
    at: str | None = None
    every: str | None = None
    anchor: str | None = None
    expression: str | None = None
    timezone: str | None = None


class Schedule(Resource):
    """Planning intent: create + start a new Story from a Workflow Definition at
    each occurrence. Holds Planning ids only; runtime-aware rules live in the
    ScheduleService process manager."""

    initiative_id: str
    name: str
    workflow_definition_id: str
    template_input: dict = {}
    story_title_template: str = "{name} · {date}"
    spec: ScheduleSpec
    overlap_policy: OverlapPolicy = OverlapPolicy.SKIP
    catch_up_window: str = "PT1H"
    keep_completed: int = 5
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    pause_reason: SchedulePauseReason | None = None
    consecutive_failures: int = 0
    next_occurrence_at: str | None = None
    created_by: str


class ScheduleRun(Schema):
    """Permanent record of one occurrence. `outcome` (the Story Execution's
    status) is filled in by queries only; it is never a stored fact."""

    id: str
    schedule_id: str
    scheduled_for: str
    fired_at: str
    status: ScheduleRunStatus
    reason: str | None = None
    story_id: str | None = None
    error: str | None = None
    settled_at: str | None = None  # set once the run's terminal outcome was processed
    outcome: StoryExecutionStatus | None = None


class ScheduleView(Schema):
    schedule: Schedule
    sentence: str
    next_occurrences: list[str] = []
    last_run: ScheduleRun | None = None


class SchedulePreview(Schema):
    sentence: str
    next_occurrences: list[str]


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
    actions: list[DecisionKind] = []


class Decision(Schema):
    id: str
    human_request_id: str
    decision: DecisionKind
    selected_option: str | None = None
    comment: str | None = None
    action_name: str | None = None
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
    status: NotificationStatus
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


class InitiativeSummary(Schema):
    """Lightweight board-list row: no columns, just counts for the header."""

    initiative: Initiative
    epic_id: str
    story_count: int
    open_human_requests: int
