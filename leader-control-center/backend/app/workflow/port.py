"""WorkflowEngine port (specs/workflow-engine/workflow-engine.md). Business logic
depends only on this interface; the in-process SimulationEngine is the MVP
adapter, and a Temporal adapter implements the same protocol later. Engine
concepts (WorkflowId/RunId/Activity) never appear in this contract."""
from __future__ import annotations

from typing import Protocol

from app.domain.models import StoryExecution


class WorkflowEngine(Protocol):
    def start_story(self, story_id: str) -> StoryExecution:
        """Create + start a Story Execution."""

    def start_task(self, task_id: str) -> None:
        """Start a single Task Execution within its Story Execution."""

    def signal(self, execution_id: str, signal: str, payload: dict | None = None) -> None:
        """Deliver a decision/control signal to a waiting execution."""

    def cancel(self, execution_id: str) -> None:
        """Cancel a running execution."""
