"""Domain enums. Values match the frontend contract (frontend/src/types/domain.ts)
exactly so JSON serialization is identical."""
from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """str-based enum: serializes to its value."""

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.value


# --- Planning -------------------------------------------------------------
class PlanningStatus(StrEnum):
    DRAFT = "Draft"
    READY = "Ready"
    ARCHIVED = "Archived"
    DELETED = "Deleted"  # soft-delete: filtered out of every API response


class TaskPlanningStatus(StrEnum):
    DRAFT = "Draft"
    READY = "Ready"
    CANCELLED = "Cancelled"


class PlanningMode(StrEnum):
    STRUCTURED = "Structured"
    GOAL_ORIENTED = "GoalOriented"


# --- Catalog --------------------------------------------------------------
class ProviderType(StrEnum):
    LLM = "llm"
    MCP = "mcp"
    HUMAN = "human"
    ACTIVITY = "activity"


# --- Runtime --------------------------------------------------------------
class StoryExecutionStatus(StrEnum):
    CREATED = "Created"
    RUNNING = "Running"
    WAITING = "Waiting"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"


class TaskExecutionStatus(StrEnum):
    CREATED = "Created"
    RUNNING = "Running"
    WAITING_DECISION = "WaitingDecision"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class CapabilityExecutionStatus(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    WAITING = "Waiting"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ProviderExecutionStatus(StrEnum):
    SCHEDULED = "Scheduled"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class ExecutionStrategy(StrEnum):
    SINGLE_PROVIDER = "SingleProvider"
    RETRY = "Retry"
    PARALLEL = "Parallel"
    CONSENSUS = "Consensus"
    HUMAN_REVIEW = "HumanReview"
    PIPELINE = "Pipeline"
    LOOP = "Loop"
    FAN_OUT = "FanOut"


# --- Human interaction ----------------------------------------------------
class HumanRequestType(StrEnum):
    APPROVAL = "Approval"
    CLARIFICATION = "Clarification"
    BUDGET = "Budget"
    TOOL_PERMISSION = "ToolPermission"
    MISSING_INFORMATION = "MissingInformation"
    CHOOSE_OPTION = "ChooseOption"
    RISK_ACCEPTANCE = "RiskAcceptance"


class HumanRequestStatus(StrEnum):
    CREATED = "Created"
    VISIBLE = "Visible"
    ACKNOWLEDGED = "Acknowledged"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class DecisionKind(StrEnum):
    APPROVE = "Approve"
    REJECT = "Reject"
    CLARIFY = "Clarify"
    CONTINUE = "Continue"
    ABORT = "Abort"
    RETRY = "Retry"
    SELECT_OPTION = "SelectOption"
    CUSTOM = "Custom"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# --- Notifications --------------------------------------------------------
class NotificationStatus(StrEnum):
    UNREAD = "UNREAD"
    READ = "READ"
    ACKED = "ACKED"
    CLOSED = "CLOSED"


# --- Artifacts & Timeline -------------------------------------------------
class ArtifactType(StrEnum):
    MARKDOWN = "Markdown"
    DOCUMENT = "Document"
    SPECIFICATION = "Specification"
    PRESENTATION = "Presentation"
    SPREADSHEET = "Spreadsheet"
    DIAGRAM = "Diagram"
    IMAGE = "Image"
    PDF = "PDF"
    SOURCE_CODE = "SourceCode"
    TEST_REPORT = "TestReport"
    RESEARCH = "Research"
    ARCHITECTURE = "Architecture"
    JSON = "JSON"


class TimelineEventCategory(StrEnum):
    RUNTIME = "Runtime"
    DECISION = "Decision"
    ARTIFACT = "Artifact"
    SYSTEM = "System"


# --- Board projection -----------------------------------------------------
class BoardColumn(StrEnum):
    TODO = "Todo"
    READY = "Ready"
    RUNNING = "Running"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"


# --- Schedules (specs/planning/schedules.md) -----------------------------
class ScheduleSpecKind(StrEnum):
    ONCE = "Once"
    INTERVAL = "Interval"
    CRON = "Cron"


class ScheduleStatus(StrEnum):
    ACTIVE = "Active"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class SchedulePauseReason(StrEnum):
    MANUAL = "Manual"
    CONSECUTIVE_FAILURES = "ConsecutiveFailures"
    INVALID_TEMPLATE = "InvalidTemplate"


class OverlapPolicy(StrEnum):
    SKIP = "Skip"
    BUFFER_ONE = "BufferOne"
    ALLOW_PARALLEL = "AllowParallel"


class ScheduleRunStatus(StrEnum):
    STARTED = "Started"
    BUFFERED = "Buffered"
    SKIPPED = "Skipped"
    MISSED = "Missed"
    FAILED_TO_START = "FailedToStart"


# --- Activity Definitions (specs/execution/activity-definitions.md) ------
class ActivityKind(StrEnum):
    BASH = "Bash"
    WEBHOOK = "Webhook"


class WebhookMethod(StrEnum):
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
