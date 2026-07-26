import type {
  Artifact,
  Capability,
  Decision,
  DecisionKind,
  HumanRequest,
  InitiativeBoardView,
  Notification,
  Provider,
  StoryExecution,
  Task,
  TimelineEvent,
} from "@/types/domain";

export interface DecisionInput {
  decision: DecisionKind;
  comment?: string;
  selectedOption?: string;
}

/**
 * The command-oriented API surface consumed by the UI.
 * Mirrors specs/api/rest-api.md. Implemented by the HTTP client and the mock.
 */
export interface ApiClient {
  // Queries
  getBoards(): Promise<InitiativeBoardView[]>;
  getStoryTasks(storyId: string): Promise<Task[]>;
  getExecution(executionId: string): Promise<StoryExecution>;
  getTimeline(storyExecutionId: string): Promise<TimelineEvent[]>;
  getArtifacts(storyId: string): Promise<Artifact[]>;
  getArtifact(artifactId: string): Promise<Artifact>;
  getAttention(): Promise<HumanRequest[]>;
  getDecisions(storyExecutionId: string): Promise<Decision[]>;
  getCapabilities(): Promise<Capability[]>;
  getProviders(): Promise<Provider[]>;
  getNotifications(): Promise<Notification[]>;

  // Planning commands
  markTaskReady(taskId: string): Promise<void>;

  // Execution commands
  startStory(storyId: string): Promise<StoryExecution>;
  startTask(taskId: string): Promise<void>;
  cancelExecution(executionId: string): Promise<void>;
  retryExecution(executionId: string): Promise<void>;

  // Decision commands (resolve the execution's open Human Request)
  submitDecision(humanRequestId: string, input: DecisionInput): Promise<Decision>;

  // Notifications
  dismissNotification(notificationId: string): Promise<void>;
}
