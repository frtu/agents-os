import type {
  Artifact,
  Capability,
  CreateStoryInput,
  Decision,
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
} from "@/types/domain";
import type { ApiClient, DecisionInput } from "@/api/types";
import { mockServer } from "@/api/mock/server";

// Seed eagerly so any query (including deep-linked pages that never hit
// getInitiatives) returns data on its first call, not only after a realtime tick.
mockServer.ensureSeeded();

/** Simulate a little network latency so loading states are exercised. */
function delay<T>(value: T, ms = 120): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const mockClient: ApiClient = {
  // Queries
  getInitiatives: (): Promise<InitiativeSummary[]> => delay(mockServer.getInitiatives()),
  getBoard: (initiativeId: string): Promise<InitiativeBoardView> => delay(mockServer.getBoard(initiativeId)),
  getStoryTasks: (storyId: string): Promise<Task[]> => delay(mockServer.getStoryTasks(storyId)),
  getExecution: (executionId: string): Promise<StoryExecution> => delay(mockServer.getExecution(executionId)),
  getTimeline: (storyExecutionId: string): Promise<TimelineEvent[]> => delay(mockServer.getTimeline(storyExecutionId)),
  getArtifacts: (storyId: string): Promise<Artifact[]> => delay(mockServer.getArtifacts(storyId)),
  getArtifact: (artifactId: string): Promise<Artifact> => delay(mockServer.getArtifact(artifactId)),
  getAttention: (): Promise<HumanRequest[]> => delay(mockServer.getAttention()),
  getOpenDecisions: (executionId: string): Promise<HumanRequest[]> => delay(mockServer.getOpenDecisions(executionId)),
  getDecisionHistory: (executionId: string): Promise<Decision[]> => delay(mockServer.getDecisionHistory(executionId)),
  getCapabilities: (): Promise<Capability[]> => delay(mockServer.getCapabilities()),
  getProviders: (): Promise<Provider[]> => delay(mockServer.getProviders()),
  getNotifications: (): Promise<Notification[]> => delay(mockServer.getNotifications()),

  // Planning commands
  createInitiative: (input): Promise<Initiative> => delay(mockServer.createInitiative(input)),
  reorderInitiatives: (initiativeIds: string[]): Promise<InitiativeSummary[]> =>
    delay(mockServer.reorderInitiatives(initiativeIds)),
  deleteInitiative: (initiativeId: string): Promise<void> => delay(mockServer.deleteInitiative(initiativeId)),
  createStory: (input: CreateStoryInput): Promise<Story> => delay(mockServer.createStory(input)),
  draftStory: (input: { initiativeId: string; message: string }): Promise<StoryDraft> =>
    delay(mockServer.draftStory(input), 400),
  markTaskReady: (taskId: string): Promise<void> => delay(mockServer.markTaskReady(taskId)),

  // Execution commands
  startStory: (storyId: string): Promise<StoryExecution> => delay(mockServer.startStory(storyId)),
  startTask: (taskId: string): Promise<void> => delay(mockServer.startTask(taskId)),
  cancelExecution: (executionId: string): Promise<void> => delay(mockServer.cancelExecution(executionId)),
  retryExecution: (executionId: string): Promise<void> => delay(mockServer.retryExecution(executionId)),

  // Decisions
  submitDecision: (_executionId: string, decisionId: string, input: DecisionInput): Promise<Decision> =>
    delay(mockServer.submitDecision(decisionId, input)),

  // Notifications (lifecycle: UNREAD -> READ -> ACKED -> CLOSED)
  openNotification: (notificationId: string): Promise<void> => delay(mockServer.openNotification(notificationId)),
  ackNotification: (notificationId: string): Promise<void> => delay(mockServer.ackNotification(notificationId)),
  closeNotification: (notificationId: string): Promise<void> => delay(mockServer.closeNotification(notificationId)),
};
