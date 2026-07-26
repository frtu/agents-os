from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.application.service import ControlCenter
from app.domain.models import InitiativeBoardView

router = APIRouter(tags=["boards"])


@router.get("/initiatives", response_model=list[InitiativeBoardView])
async def list_boards(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_boards()
