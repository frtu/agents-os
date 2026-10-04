import type {
  Artifact,
  Capability,
  CreateStoryInput,
  UpdateInitiativeInput,
  UpdateStoryInput,
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
  CreateScheduleInput,
  ScheduleView,
  SchedulePreview,
  SchedulePreviewInput,
  ScheduleRun,
  UpdateScheduleInput,
  ActivityDefinition,
  ActivityDefinitionInput,
  RenderedActivity,
  WebhookTestResult,
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
  updateInitiative(
    initiativeId: string,
    input: UpdateInitiativeInput,
  ): Promise<Initiative>;
  reorderInitiatives(initiativeIds: string[]): Promise<InitiativeSummary[]>;
  // Soft-delete an initiative; its stories are reparented onto the Misc initiative.
  deleteInitiative(initiativeId: string): Promise<void>;
  createStory(input: CreateStoryInput): Promise<Story>;
  updateStory(storyId: string, input: UpdateStoryInput): Promise<Story>;
  // Soft-delete a story; it drops out of every board projection.
  deleteStory(storyId: string): Promise<void>;
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

  // Schedules (time-triggered Stories)
  getSchedules(initiativeId?: string): Promise<ScheduleView[]>;
  getSchedule(scheduleId: string): Promise<ScheduleView>;
  getScheduleRuns(scheduleId: string): Promise<ScheduleRun[]>;
  previewSchedule(input: SchedulePreviewInput): Promise<SchedulePreview>;
  createSchedule(input: CreateScheduleInput): Promise<ScheduleView>;
  updateSchedule(scheduleId: string, input: UpdateScheduleInput): Promise<ScheduleView>;
  pauseSchedule(scheduleId: string): Promise<ScheduleView>;
  resumeSchedule(scheduleId: string): Promise<ScheduleView>;
  // "Run now": one out-of-band occurrence; the next natural one is unchanged.
  triggerSchedule(scheduleId: string): Promise<ScheduleRun>;
  archiveSchedule(scheduleId: string): Promise<ScheduleView>;

  // Activity Definitions (UI "Tasks"): reusable bash / webhook building blocks
  getActivityDefinitions(): Promise<ActivityDefinition[]>;
  createActivityDefinition(input: ActivityDefinitionInput): Promise<ActivityDefinition>;
  updateActivityDefinition(id: string, input: ActivityDefinitionInput): Promise<ActivityDefinition>;
  deleteActivityDefinition(id: string): Promise<void>;
  // Apply parameters with no side effects (secrets stay masked).
  renderActivityDefinition(id: string, input: Record<string, unknown>): Promise<RenderedActivity>;
  // Send a webhook once (Webhook only; bash runs on a Temporal worker).
  testActivityDefinition(id: string, input: Record<string, unknown>): Promise<WebhookTestResult>;
}
