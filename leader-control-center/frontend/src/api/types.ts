import type {
  Artifact,
  Capability,
  CreateStoryInput,
  Decision,
  DecisionKind,
  HumanRequest,
  Initiative,
  InitiativeBoardView,
  InitiativeSummary,
  Notification,
  Provider,
  Story,
  StoryDraft,
  StoryExecution,
  Task,
  TimelineEvent,
  WorkflowDefinition,
  CreateWorkflowDefinitionInput,
  UpdateWorkflowDefinitionInput,
} from "@/types/domain";

export interface DecisionInput {
  decision: DecisionKind;
  comment?: string;
  selectedOption?: string;
  actionName?: string;
}

/**
 * The command-oriented API surface consumed by the UI.
 * Mirrors specs/api/rest-api.md. Implemented by the HTTP client and the mock.
 */
export interface ApiClient {
  // Queries
  getInitiatives(): Promise<InitiativeSummary[]>;
  getBoard(initiativeId: string): Promise<InitiativeBoardView>;
  getStoryTasks(storyId: string): Promise<Task[]>;
  getExecution(executionId: string): Promise<StoryExecution>;
  getTimeline(storyExecutionId: string): Promise<TimelineEvent[]>;
  getArtifacts(storyId: string): Promise<Artifact[]>;
  getArtifact(artifactId: string): Promise<Artifact>;
  getAttention(): Promise<HumanRequest[]>;
  // Open decisions-to-make for an execution (each with its action enum).
  getOpenDecisions(executionId: string): Promise<HumanRequest[]>;
  // Recorded, immutable decisions (audit trail) for an execution.
  getDecisionHistory(executionId: string): Promise<Decision[]>;
  getCapabilities(): Promise<Capability[]>;
  getProviders(): Promise<Provider[]>;
  getNotifications(): Promise<Notification[]>;
  getWorkflowDefinitions(): Promise<WorkflowDefinition[]>;
  getWorkflowDefinition(wdId: string): Promise<WorkflowDefinition>;

  // Planning commands
  createInitiative(input: {
    title: string;
    description?: string;
    workflowDefinitionId?: string;
  }): Promise<Initiative>;
  reorderInitiatives(initiativeIds: string[]): Promise<InitiativeSummary[]>;
  // Soft-delete an initiative; its stories are reparented onto the Misc initiative.
  deleteInitiative(initiativeId: string): Promise<void>;
  createStory(input: CreateStoryInput): Promise<Story>;
  // LLM-assisted prefill: turn a free-text brief into draft story fields.
  draftStory(input: { initiativeId: string; message: string }): Promise<StoryDraft>;
  markTaskReady(taskId: string): Promise<void>;

  // Execution commands
  startStory(storyId: string): Promise<StoryExecution>;
  startTask(taskId: string): Promise<void>;
  cancelExecution(executionId: string): Promise<void>;
  retryExecution(executionId: string): Promise<void>;

  // Decision commands (resolve an execution's open decision-to-make)
  submitDecision(executionId: string, decisionId: string, input: DecisionInput): Promise<Decision>;

  // Notifications (lifecycle: UNREAD -> READ -> ACKED -> CLOSED)
  openNotification(notificationId: string): Promise<void>;
  ackNotification(notificationId: string): Promise<void>;
  closeNotification(notificationId: string): Promise<void>;

  // Workflow definition commands (authoring-time blueprints)
  createWorkflowDefinition(input: CreateWorkflowDefinitionInput): Promise<WorkflowDefinition>;
  updateWorkflowDefinition(
    wdId: string,
    input: UpdateWorkflowDefinitionInput,
  ): Promise<WorkflowDefinition>;
  // Blocked with 409 if the definition is still referenced by planning objects.
  deleteWorkflowDefinition(wdId: string): Promise<void>;
}
