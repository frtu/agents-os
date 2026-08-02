from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_control_center
from app.api.schemas import CreateStoryBody, DraftStoryBody
from app.application.service import ControlCenter
from app.domain.models import Artifact, Story, StoryDraft, StoryExecution, Task

router = APIRouter(tags=["stories"])


@router.post("/stories", response_model=Story, status_code=201)
async def create_story(body: CreateStoryBody, cc: ControlCenter = Depends(get_control_center)):
    return cc.create_story(
        body.epic_id, body.title, body.description,
        body.priority, body.acceptance_criteria,
    )


@router.post("/stories/draft", response_model=StoryDraft)
async def draft_story(body: DraftStoryBody, cc: ControlCenter = Depends(get_control_center)):
    return cc.draft_story(body.initiative_id, body.message)


@router.get("/stories/{story_id}/tasks", response_model=list[Task])
async def get_story_tasks(story_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_story_tasks(story_id)


@router.get("/stories/{story_id}/artifacts", response_model=list[Artifact])
async def get_story_artifacts(story_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.get_artifacts(story_id)


@router.post("/stories/{story_id}/start", response_model=StoryExecution)
async def start_story(story_id: str, cc: ControlCenter = Depends(get_control_center)):
    return cc.start_story(story_id)
