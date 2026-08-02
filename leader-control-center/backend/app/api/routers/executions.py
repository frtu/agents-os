"""Execution queries/commands plus decision resolution. A decision-to-make is an
open Human Request on an execution; each action resolves it and records an
immutable Decision. Paths mirror specs/api/rest-api.md."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_control_center
from app.api.schemas import ClarifyBody, CustomBody, RejectBody, SelectBody
from app.application.service import ControlCenter
from app.domain.enums import DecisionKind
from app.domain.models import Decision, HumanRequest, StoryExecution, TimelineEvent

router = APIRouter(tags=["executions"])


@router.get("/executions/{execution_id}", response_model=StoryExecution)
async def get_execution(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_execution(execution_id)


@router.get("/executions/{execution_id}/timeline", response_model=list[TimelineEvent])
async def get_timeline(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_timeline(execution_id)


@router.post("/executions/{execution_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_execution(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.cancel_execution(execution_id)


@router.post("/executions/{execution_id}/retry", status_code=status.HTTP_204_NO_CONTENT)
async def retry_execution(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.retry_execution(execution_id)


# -- decisions -------------------------------------------------------------
@router.get("/executions/{execution_id}/decisions", response_model=list[HumanRequest])
async def get_open_decisions(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    """Open decisions-to-make, each with its available actions."""
    return cc.get_open_decisions(execution_id)


@router.get("/executions/{execution_id}/decisions/history", response_model=list[Decision])
async def get_decision_history(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    """Recorded, immutable decisions (audit trail)."""
    return cc.get_decision_history(execution_id)


@router.post("/executions/{execution_id}/decisions/{decision_id}/approve", response_model=Decision)
async def approve(execution_id: str, decision_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.APPROVE)


@router.post("/executions/{execution_id}/decisions/{decision_id}/reject", response_model=Decision)
async def reject(execution_id: str, decision_id: str, body: RejectBody | None = None, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.REJECT, comment=body.comment if body else None)


@router.post("/executions/{execution_id}/decisions/{decision_id}/clarify", response_model=Decision)
async def clarify(execution_id: str, decision_id: str, body: ClarifyBody | None = None, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.CLARIFY, comment=body.message if body else None)


@router.post("/executions/{execution_id}/decisions/{decision_id}/continue", response_model=Decision)
async def continue_execution(execution_id: str, decision_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.CONTINUE)


@router.post("/executions/{execution_id}/decisions/{decision_id}/abort", response_model=Decision)
async def abort(execution_id: str, decision_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.ABORT)


@router.post("/executions/{execution_id}/decisions/{decision_id}/retry", response_model=Decision)
async def retry(execution_id: str, decision_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.RETRY)


@router.post("/executions/{execution_id}/decisions/{decision_id}/select", response_model=Decision)
async def select(execution_id: str, decision_id: str, body: SelectBody | None = None, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.SELECT_OPTION, selected_option=body.option_id if body else None)


@router.post("/executions/{execution_id}/decisions/{decision_id}/custom", response_model=Decision)
async def custom(execution_id: str, decision_id: str, body: CustomBody, cc: ControlCenter = Depends(get_control_center)):
    return cc.submit_decision(decision_id, DecisionKind.CUSTOM, comment=body.comment, action_name=body.action_name)
