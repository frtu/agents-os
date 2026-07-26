from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.application.service import ControlCenter
from app.domain.models import Artifact

router = APIRouter(tags=["artifacts"])


@router.get("/artifacts/{artifact_id}", response_model=Artifact)
async def get_artifact(artifact_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_artifact(artifact_id)
