from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_control_center
from app.application.service import ControlCenter

router = APIRouter(tags=["tasks"])


@router.post("/tasks/{task_id}/ready", status_code=status.HTTP_204_NO_CONTENT)
async def mark_task_ready(task_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.mark_task_ready(task_id)


@router.post("/tasks/{task_id}/start", status_code=status.HTTP_204_NO_CONTENT)
async def start_task(task_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.start_task(task_id)
