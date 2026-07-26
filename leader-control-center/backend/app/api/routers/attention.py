from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.application.service import ControlCenter
from app.domain.models import HumanRequest

router = APIRouter(tags=["attention"])


@router.get("/attention", response_model=list[HumanRequest])
async def get_attention(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_attention()
