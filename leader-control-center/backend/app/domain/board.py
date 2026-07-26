"""Board (Kanban) projection: pure functions mapping planning status + latest
execution to a column. Mirrors the frontend projection so both render identically."""
from __future__ import annotations

from app.domain.enums import BoardColumn, PlanningStatus, StoryExecutionStatus
from app.domain.models import StoryCardView, StoryExecution, Story


def column_for(
    story: Story, execution: StoryExecution | None, open_requests: int
) -> BoardColumn:
    if execution is None:
        return (
            BoardColumn.READY
            if story.status == PlanningStatus.READY
            else BoardColumn.TODO
        )
    if (
        open_requests > 0
        or execution.status in (StoryExecutionStatus.WAITING, StoryExecutionStatus.FAILED)
    ):
        return BoardColumn.BLOCKED
    if execution.status == StoryExecutionStatus.COMPLETED:
        return BoardColumn.COMPLETED
    if execution.status == StoryExecutionStatus.CANCELLED:
        return BoardColumn.TODO
    return BoardColumn.RUNNING


def empty_columns() -> dict[BoardColumn, list[StoryCardView]]:
    return {column: [] for column in BoardColumn}
