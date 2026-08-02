"""Request bodies for decision endpoints. Response shapes reuse the domain
models directly (already camelCase). Fields are optional so a missing body is
tolerated, matching the frontend which omits bodies for approve/continue/etc."""
from __future__ import annotations

from app.domain.models import Schema


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
