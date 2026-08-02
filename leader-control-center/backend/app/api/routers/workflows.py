from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_control_center
from app.api.schemas import (
    CreateWorkflowDefinitionBody,
    UpdateWorkflowDefinitionBody,
)
from app.application.service import ControlCenter
from app.domain.models import WorkflowDefinition

router = APIRouter(tags=["workflows"])


@router.get("/workflow-definitions", response_model=list[WorkflowDefinition])
async def list_workflow_definitions(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_workflow_definitions()


@router.get("/workflow-definitions/{wd_id}", response_model=WorkflowDefinition)
async def get_workflow_definition(
    wd_id: str, cc: ControlCenter = Depends(get_control_center)
):
    return cc.get_workflow_definition(wd_id)


@router.post(
    "/workflow-definitions",
    response_model=WorkflowDefinition,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_definition(
    body: CreateWorkflowDefinitionBody, cc: ControlCenter = Depends(get_control_center)
):
    return cc.create_workflow_definition(body.name, body.input, body.definition)


@router.patch("/workflow-definitions/{wd_id}", response_model=WorkflowDefinition)
async def update_workflow_definition(
    wd_id: str,
    body: UpdateWorkflowDefinitionBody,
    cc: ControlCenter = Depends(get_control_center),
):
    return cc.update_workflow_definition(wd_id, body.name, body.input, body.definition)


@router.delete("/workflow-definitions/{wd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_definition(
    wd_id: str, cc: ControlCenter = Depends(get_control_center)
):
    cc.delete_workflow_definition(wd_id)
