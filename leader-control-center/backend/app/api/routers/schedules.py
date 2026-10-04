"""Schedules: time-triggered Story creation (specs/planning/schedules.md §API)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.api.schemas import ScheduleBody, SchedulePreviewBody, UpdateScheduleBody
from app.application.schedules import ScheduleService
from app.application.service import ControlCenter
from app.domain.models import SchedulePreview, ScheduleRun, ScheduleView

router = APIRouter(tags=["schedules"])


def _schedules(cc: ControlCenter = Depends(get_control_center)) -> ScheduleService:
    assert cc.schedules is not None, "ScheduleService not wired"
    return cc.schedules


@router.get("/schedules", response_model=list[ScheduleView])
async def list_schedules(
    initiative_id: str | None = None, include_archived: bool = False,
    svc: ScheduleService = Depends(_schedules),
):
    return svc.list_schedules(initiative_id, include_archived)


@router.post("/schedules/preview", response_model=SchedulePreview)
async def preview_schedule(
    body: SchedulePreviewBody, svc: ScheduleService = Depends(_schedules),
):
    return svc.preview(
        body.initiative_id, body.name, body.spec,
        body.overlap_policy, body.story_title_template,
    )


@router.post("/schedules", response_model=ScheduleView, status_code=201)
async def create_schedule(body: ScheduleBody, svc: ScheduleService = Depends(_schedules)):
    return svc.create(
        body.initiative_id, body.name, body.workflow_definition_id,
        body.template_input, body.spec, body.overlap_policy,
        body.catch_up_window, body.keep_completed, body.story_title_template,
        run_now=body.run_now,
    )


@router.get("/schedules/{schedule_id}", response_model=ScheduleView)
async def get_schedule(schedule_id: str, svc: ScheduleService = Depends(_schedules)):
    return svc.get(schedule_id)


@router.get("/schedules/{schedule_id}/runs", response_model=list[ScheduleRun])
async def list_runs(schedule_id: str, svc: ScheduleService = Depends(_schedules)):
    return svc.runs(schedule_id)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleView)
async def update_schedule(
    schedule_id: str, body: UpdateScheduleBody,
    svc: ScheduleService = Depends(_schedules),
):
    return svc.update(schedule_id, **body.model_dump(exclude_none=True))


@router.post("/schedules/{schedule_id}/pause", response_model=ScheduleView)
async def pause_schedule(schedule_id: str, svc: ScheduleService = Depends(_schedules)):
    return svc.pause(schedule_id)


@router.post("/schedules/{schedule_id}/resume", response_model=ScheduleView)
async def resume_schedule(schedule_id: str, svc: ScheduleService = Depends(_schedules)):
    return svc.resume(schedule_id)


@router.post("/schedules/{schedule_id}/trigger", response_model=ScheduleRun)
async def trigger_schedule(schedule_id: str, svc: ScheduleService = Depends(_schedules)):
    return svc.trigger(schedule_id)


@router.post("/schedules/{schedule_id}/archive", response_model=ScheduleView)
async def archive_schedule(schedule_id: str, svc: ScheduleService = Depends(_schedules)):
    return svc.archive(schedule_id)
