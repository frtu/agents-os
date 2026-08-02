from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_control_center
from app.api.schemas import (
    CreateInitiativeBody,
    ReorderInitiativesBody,
    UpdateInitiativeBody,
)
from app.application.service import ControlCenter
from app.domain.models import Initiative, InitiativeBoardView, InitiativeSummary

router = APIRouter(tags=["boards"])


@router.get("/initiatives", response_model=list[InitiativeSummary])
async def list_initiatives(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_initiatives()


@router.post("/initiatives", response_model=Initiative, status_code=status.HTTP_201_CREATED)
async def create_initiative(
    body: CreateInitiativeBody, cc: ControlCenter = Depends(get_control_center)
):
    return cc.create_initiative(body.title, body.description, body.workflow_definition_id)


@router.patch("/initiatives/{initiative_id}", response_model=Initiative)
async def update_initiative(
    initiative_id: str,
    body: UpdateInitiativeBody,
    cc: ControlCenter = Depends(get_control_center),
):
    return cc.update_initiative(
        initiative_id, body.title, body.description, body.workflow_definition_id
    )


@router.post("/initiatives/reorder", response_model=list[InitiativeSummary])
async def reorder_initiatives(
    body: ReorderInitiativesBody, cc: ControlCenter = Depends(get_control_center)
):
    return cc.reorder_initiatives(body.initiative_ids)


@router.post("/initiatives/{initiative_id}/delete", response_model=list[InitiativeSummary])
async def delete_initiative(
    initiative_id: str, cc: ControlCenter = Depends(get_control_center)
):
    return cc.delete_initiative(initiative_id)


@router.get("/initiatives/{initiative_id}/board", response_model=InitiativeBoardView)
async def get_board(initiative_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_board(initiative_id)
