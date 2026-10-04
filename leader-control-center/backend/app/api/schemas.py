"""Request bodies for decision endpoints. Response shapes reuse the domain
models directly (already camelCase). Fields are optional so a missing body is
tolerated, matching the frontend which omits bodies for approve/continue/etc."""
from __future__ import annotations

from app.domain.enums import ActivityKind, OverlapPolicy, WebhookMethod
from app.domain.models import Schema, ScheduleSpec


class RejectBody(Schema):
    comment: str | None = None


class ClarifyBody(Schema):
    message: str | None = None


class SelectBody(Schema):
    option_id: str | None = None


class CustomBody(Schema):
    action_name: str
    comment: str | None = None


class CreateInitiativeBody(Schema):
    title: str
    description: str = ""
    workflow_definition_id: str | None = None


class UpdateInitiativeBody(Schema):
    title: str
    description: str = ""
    workflow_definition_id: str | None = None


class ReorderInitiativesBody(Schema):
    initiative_ids: list[str]


class CreateStoryBody(Schema):
    epic_id: str
    title: str
    description: str = ""
    priority: int = 1
    acceptance_criteria: list[str] = []
    workflow_definition_id: str | None = None
    template_input: dict | None = None


class UpdateStoryBody(Schema):
    title: str
    description: str = ""
    priority: int = 1
    acceptance_criteria: list[str] = []


class DraftStoryBody(Schema):
    initiative_id: str
    message: str


class CreateWorkflowDefinitionBody(Schema):
    name: str
    input: dict = {}
    definition: str = ""


class UpdateWorkflowDefinitionBody(Schema):
    name: str | None = None
    input: dict | None = None
    definition: str | None = None


class ScheduleBody(Schema):
    """Create-schedule request (specs/planning/schedules.md §API)."""

    initiative_id: str
    name: str
    workflow_definition_id: str
    template_input: dict = {}
    spec: ScheduleSpec
    overlap_policy: OverlapPolicy = OverlapPolicy.SKIP
    catch_up_window: str = "PT1H"
    keep_completed: int = 5
    story_title_template: str = "{name} · {date}"
    run_now: bool = False


class SchedulePreviewBody(Schema):
    initiative_id: str
    name: str = ""
    spec: ScheduleSpec
    overlap_policy: OverlapPolicy = OverlapPolicy.SKIP
    story_title_template: str = "{name} · {date}"


class UpdateScheduleBody(Schema):
    name: str | None = None
    workflow_definition_id: str | None = None
    template_input: dict | None = None
    spec: ScheduleSpec | None = None
    overlap_policy: OverlapPolicy | None = None
    catch_up_window: str | None = None
    keep_completed: int | None = None
    story_title_template: str | None = None


class ActivityDefinitionBody(Schema):
    """Create (all editable fields) or update (any subset) an Activity Definition."""

    name: str | None = None
    description: str | None = None
    kind: ActivityKind | None = None
    input: dict | None = None
    timeout_seconds: int | None = None
    script: str | None = None
    method: WebhookMethod | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    content_type: str | None = None
    body_template: str | None = None


class ActivityInputBody(Schema):
    input: dict = {}
