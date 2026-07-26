from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_control_center
from app.application.service import ControlCenter
from app.domain.models import Notification

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[Notification])
async def get_notifications(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_notifications()


@router.post("/notifications/{notification_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_notification(notification_id: str, cc: ControlCenter = Depends(get_control_center)):
    cc.dismiss_notification(notification_id)
