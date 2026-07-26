from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.application.service import ControlCenter
from app.domain.models import Capability, Provider

router = APIRouter(tags=["catalog"])


@router.get("/capabilities", response_model=list[Capability])
async def get_capabilities(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_capabilities()


@router.get("/providers", response_model=list[Provider])
async def get_providers(cc: ControlCenter = Depends(get_control_center)):
    return cc.get_providers()
