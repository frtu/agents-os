"""Activity Definitions — UI menu "Tasks" (specs/execution/activity-definitions.md)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_control_center
from app.api.schemas import ActivityDefinitionBody, ActivityInputBody
from app.application.activities import ActivityDefinitionService
from app.application.service import ControlCenter
from app.domain.models import ActivityDefinition, RenderedActivity, WebhookTestResult

router = APIRouter(tags=["activity-definitions"])


def _activities(cc: ControlCenter = Depends(get_control_center)) -> ActivityDefinitionService:
    return cc.activities


@router.get("/activity-definitions", response_model=list[ActivityDefinition])
async def list_definitions(svc: ActivityDefinitionService = Depends(_activities)):
    return svc.list_definitions()


@router.get("/activity-definitions/{definition_id}", response_model=ActivityDefinition)
async def get_definition(definition_id: str, svc: ActivityDefinitionService = Depends(_activities)):
    return svc.get(definition_id)


@router.post("/activity-definitions", response_model=ActivityDefinition, status_code=201)
async def create_definition(
    body: ActivityDefinitionBody, svc: ActivityDefinitionService = Depends(_activities),
):
    return svc.create(**body.model_dump(exclude_none=True))


@router.patch("/activity-definitions/{definition_id}", response_model=ActivityDefinition)
async def update_definition(
    definition_id: str, body: ActivityDefinitionBody,
    svc: ActivityDefinitionService = Depends(_activities),
):
    return svc.update(definition_id, **body.model_dump(exclude_none=True))


@router.delete("/activity-definitions/{definition_id}", status_code=204)
async def delete_definition(definition_id: str, svc: ActivityDefinitionService = Depends(_activities)):
    svc.delete(definition_id)
    return Response(status_code=204)


@router.post("/activity-definitions/{definition_id}/render", response_model=RenderedActivity)
async def render_definition(
    definition_id: str, body: ActivityInputBody,
    svc: ActivityDefinitionService = Depends(_activities),
):
    return svc.render(definition_id, body.input)


# Sync handler: FastAPI runs it in the threadpool, so the outbound HTTP call
# does not block the event loop (and the simulation/scheduler ticks).
@router.post("/activity-definitions/{definition_id}/test", response_model=WebhookTestResult)
def test_definition(
    definition_id: str, body: ActivityInputBody,
    svc: ActivityDefinitionService = Depends(_activities),
):
    return svc.test_webhook(definition_id, body.input)
