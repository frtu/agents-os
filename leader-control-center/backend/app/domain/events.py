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


class RealtimeMessage(Schema):
    type: MessageType
    aggregate_id: str
    sequence: int
    payload: dict | None = None
