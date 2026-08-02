/**
 * Domain types mirroring specs/domain and specs/execution.
 * Planning is immutable intent; Runtime is disposable execution; History is permanent.
 */

// ---------------------------------------------------------------------------
// Shared
// ---------------------------------------------------------------------------

export interface Resource {
  id: string;
  version: number;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Planning (immutable intent)
// ---------------------------------------------------------------------------

export type PlanningStatus = "Draft" | "Ready" | "Archived";
export type TaskPlanningStatus = "Draft" | "Ready" | "Cancelled";
export type PlanningMode = "Structured" | "GoalOriented";

export interface Initiative extends Resource {
  portfolioId: string;
  title: string;
  description: string;
  status: PlanningStatus;
  order: number;
}

export interface Epic extends Resource {
  initiativeId: string;
  title: string;
  description: string;
  status: PlanningStatus;
}

export interface Story extends Resource {
  epicId: string;
  title: string;
  description: string;
  priority: number;
  status: PlanningStatus;
  acceptanceCriteria: AcceptanceCriteria[];
}

export interface AcceptanceCriteria {
  id: string;
  description: string;
}

// LLM-assisted prefill for the create-story form (not a stored resource).
export interface StoryDraft {
  title: string;
  description: string;
  priority: number;
  acceptanceCriteria: string[];
}

export interface CreateStoryInput {
  epicId: string;
  title: string;
  description?: string;
  priority?: number;
  acceptanceCriteria?: string[];
}

export interface Task extends Resource {
  storyId: string;
  name: string;
  planningMode: PlanningMode;
  status: TaskPlanningStatus;
  order: number;
  dependencies: string[];
  // Structured
  capabilityId?: string;
  // Goal-Oriented
  goal?: string;
  successCriteria?: string[];
}

// ---------------------------------------------------------------------------
// Catalog
// ---------------------------------------------------------------------------

export interface Capability {
  id: string;
  name: string;
  description: string;
  inputs: string;
  outputs: string;
  supportedProviders: string[];
}

export type ProviderType = "llm" | "mcp" | "human" | "activity";

export interface Provider {
  id: string;
  name: string;
  type: ProviderType;
}

// ---------------------------------------------------------------------------
// Runtime (disposable execution)
// ---------------------------------------------------------------------------

export type StoryExecutionStatus =
  | "Created"
  | "Running"
  | "Waiting"
  | "Completed"
  | "Cancelled"
  | "Failed";

export type TaskExecutionStatus =
  | "Created"
  | "Running"
  | "WaitingDecision"
  | "Completed"
  | "Failed"
  | "Cancelled";

export type CapabilityExecutionStatus =
  | "Pending"
  | "Running"
  | "Waiting"
  | "Completed"
  | "Failed";

export type ProviderExecutionStatus =
  | "Scheduled"
  | "Running"
  | "Succeeded"
  | "Failed"
  | "Cancelled";

export type ExecutionStrategy =
  | "SingleProvider"
  | "Retry"
  | "Parallel"
  | "Consensus"
  | "HumanReview"
  | "Pipeline"
  | "Loop"
  | "FanOut";

export interface ProviderExecution {
  id: string;
  capabilityExecutionId: string;
  providerId: string;
  providerName: string;
  status: ProviderExecutionStatus;
  attempt: number;
  startedAt?: string;
  endedAt?: string;
}

export interface CapabilityExecution {
  id: string;
  taskExecutionId: string;
  capabilityId: string;
  capabilityName: string;
  strategy: ExecutionStrategy;
  status: CapabilityExecutionStatus;
  providerExecutions: ProviderExecution[];
}

export interface TaskExecution {
  id: string;
  storyExecutionId: string;
  taskId: string;
  taskName: string;
  status: TaskExecutionStatus;
  attempt: number;
  waitingReason?: string;
  startedAt?: string;
  completedAt?: string;
  capabilityExecutions: CapabilityExecution[];
}

export interface StoryExecution {
  id: string;
  storyId: string;
  status: StoryExecutionStatus;
  progress: number; // 0..1
  startedAt?: string;
  completedAt?: string;
  taskExecutions: TaskExecution[];
}

// ---------------------------------------------------------------------------
// Human interaction
// ---------------------------------------------------------------------------

export type HumanRequestType =
  | "Approval"
  | "Clarification"
  | "Budget"
  | "ToolPermission"
  | "MissingInformation"
  | "ChooseOption"
  | "RiskAcceptance";

export type HumanRequestStatus =
  | "Created"
  | "Visible"
  | "Acknowledged"
  | "Resolved"
  | "Closed";

export type DecisionKind =
  | "Approve"
  | "Reject"
  | "Clarify"
  | "Continue"
  | "Abort"
  | "Retry"
  | "SelectOption"
  | "Custom";

export interface HumanRequestOption {
  id: string;
  label: string;
}

export interface HumanRequest {
  id: string;
  executionId: string;
  initiativeId: string;
  initiativeTitle: string;
  storyId: string;
  storyTitle: string;
  type: HumanRequestType;
  prompt: string;
  options?: HumanRequestOption[];
  status: HumanRequestStatus;
  priority: "low" | "medium" | "high";
  createdAt: string;
  // Actions this open decision-to-make accepts; the UI renders exactly these.
  actions: DecisionKind[];
}

export interface Decision {
  id: string;
  humanRequestId: string;
  decision: DecisionKind;
  selectedOption?: string;
  comment?: string;
  actionName?: string;
  user: string;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Artifacts & Timeline
// ---------------------------------------------------------------------------

export type ArtifactType =
  | "Markdown"
  | "Document"
  | "Specification"
  | "Presentation"
  | "Spreadsheet"
  | "Diagram"
  | "Image"
  | "PDF"
  | "SourceCode"
  | "TestReport"
  | "Research"
  | "Architecture"
  | "JSON";

export interface Artifact {
  id: string;
  executionId: string;
  storyId: string;
  type: ArtifactType;
  name: string;
  version: number;
  createdBy: string;
  createdAt: string;
  parentArtifactId?: string;
  // Inline preview content for the mock backend / simple renderers.
  content?: string;
  language?: string;
}

export type TimelineEventCategory =
  | "Runtime"
  | "Decision"
  | "Artifact"
  | "System";

export interface TimelineEvent {
  id: string;
  executionId: string;
  type: string;
  category: TimelineEventCategory;
  detail?: string;
  occurredAt: string;
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export type NotificationStatus = "UNREAD" | "READ" | "ACKED" | "CLOSED";

export interface Notification {
  id: string;
  type: string;
  message: string;
  status: NotificationStatus;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Board projection (UI-only combination of planning + latest execution)
// ---------------------------------------------------------------------------

export type BoardColumn =
  | "Todo"
  | "Ready"
  | "Running"
  | "Blocked"
  | "Completed";

export interface StoryCardView {
  story: Story;
  column: BoardColumn;
  execution?: StoryExecution;
  openHumanRequests: number;
}

export interface InitiativeBoardView {
  initiative: Initiative;
  epicId: string;
  columns: Record<BoardColumn, StoryCardView[]>;
  openHumanRequests: number;
}

export interface InitiativeSummary {
  initiative: Initiative;
  epicId: string;
  storyCount: number;
  openHumanRequests: number;
}
