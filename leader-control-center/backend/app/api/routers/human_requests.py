"""Decision endpoints. Each resolves an open Human Request and returns the
recorded Decision. Paths mirror the frontend's decisionEndpoint() mapping."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.api.schemas import ClarifyBody, RejectBody, SelectBody
from app.application.service import ControlCenter
from app.domain.enums import DecisionKind
from app.domain.models import Decision

router = APIRouter(prefix="/human-requests", tags=["decisions"])


@router.post("/{request_id}/approve", response_model=Decision)
async def approve(request_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.APPROVE)


@router.post("/{request_id}/reject", response_model=Decision)
async def reject(request_id: str, body: RejectBody | None = None, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.REJECT, comment=body.comment if body else None)


@router.post("/{request_id}/clarify", response_model=Decision)
async def clarify(request_id: str, body: ClarifyBody | None = None, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.CLARIFY, comment=body.message if body else None)


@router.post("/{request_id}/continue", response_model=Decision)
async def continue_execution(request_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.CONTINUE)


@router.post("/{request_id}/abort", response_model=Decision)
async def abort(request_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.ABORT)


@router.post("/{request_id}/retry", response_model=Decision)
async def retry(request_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.RETRY)


@router.post("/{request_id}/select", response_model=Decision)
async def select(request_id: str, body: SelectBody | None = None, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(request_id, DecisionKind.SELECT_OPTION, selected_option=body.option_id if body else None)
