"""Realtime message contract (specs/api/realtime.md). Server->client messages
are projections of domain events; the wire shape matches
frontend/src/realtime/types.ts: { type, aggregateId, sequence, payload? }."""
from __future__ import annotations

from app.domain.enums import StrEnum
from app.domain.models import Schema


class MessageType(StrEnum):
    STORY_UPDATED = "StoryUpdated"
    EXECUTION_UPDATED = "ExecutionUpdated"
    TIMELINE_UPDATED = "TimelineUpdated"
    DECISION_REQUESTED = "DecisionRequested"
    DECISION_APPLIED = "DecisionApplied"
    ARTIFACT_PRODUCED = "ArtifactProduced"
    ATTENTION_UPDATED = "AttentionUpdated"
    NOTIFICATION_CREATED = "NotificationCreated"
    WORKFLOW_DEFINITION_UPDATED = "WorkflowDefinitionUpdated"
    SCHEDULE_UPDATED = "ScheduleUpdated"
    SCHEDULE_RUN_RECORDED = "ScheduleRunRecorded"
    ACTIVITY_DEFINITION_UPDATED = "ActivityDefinitionUpdated"


class RealtimeMessage(Schema):
    type: MessageType
    aggregate_id: str
    sequence: int
    payload: dict | None = None
