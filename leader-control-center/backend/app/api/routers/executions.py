from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_control_center
from app.application.service import ControlCenter
from app.domain.models import Decision, StoryExecution, TimelineEvent

router = APIRouter(tags=["executions"])


@router.get("/executions/{execution_id}", response_model=StoryExecution)
async def get_execution(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_execution(execution_id)


@router.get("/executions/{execution_id}/timeline", response_model=list[TimelineEvent])
async def get_timeline(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_timeline(execution_id)


@router.get("/executions/{execution_id}/decisions", response_model=list[Decision])
async def get_decisions(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_decisions(execution_id)


@router.post("/executions/{execution_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_execution(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.cancel_execution(execution_id)


@router.post("/executions/{execution_id}/retry", status_code=status.HTTP_204_NO_CONTENT)
async def retry_execution(execution_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.retry_execution(execution_id)
