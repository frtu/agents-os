import type {
  Artifact,
  Capability,
  Decision,
  HumanRequest,
  InitiativeBoardView,
  Notification,
  Provider,
  StoryExecution,
  Task,
  TimelineEvent,
} from "@/types/domain";
import type { ApiClient, DecisionInput } from "@/api/types";
import { mockServer } from "@/api/mock/server";

// Seed eagerly so any query (including deep-linked pages that never hit
// getBoards) returns data on its first call, not only after a realtime tick.
mockServer.ensureSeeded();

/** Simulate a little network latency so loading states are exercised. */
function delay<T>(value: T, ms = 120): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const mockClient: ApiClient = {
  // Queries
  getBoards: (): Promise<InitiativeBoardView[]> => delay(mockServer.getBoards()),
  getStoryTasks: (storyId: string): Promise<Task[]> => delay(mockServer.getStoryTasks(storyId)),
  getExecution: (executionId: string): Promise<StoryExecution> => delay(mockServer.getExecution(executionId)),
  getTimeline: (storyExecutionId: string): Promise<TimelineEvent[]> => delay(mockServer.getTimeline(storyExecutionId)),
  getArtifacts: (storyId: string): Promise<Artifact[]> => delay(mockServer.getArtifacts(storyId)),
  getArtifact: (artifactId: string): Promise<Artifact> => delay(mockServer.getArtifact(artifactId)),
  getAttention: (): Promise<HumanRequest[]> => delay(mockServer.getAttention()),
  getDecisions: (storyExecutionId: string): Promise<Decision[]> => delay(mockServer.getDecisions(storyExecutionId)),
  getCapabilities: (): Promise<Capability[]> => delay(mockServer.getCapabilities()),
  getProviders: (): Promise<Provider[]> => delay(mockServer.getProviders()),
  getNotifications: (): Promise<Notification[]> => delay(mockServer.getNotifications()),

  // Planning commands
  markTaskReady: (taskId: string): Promise<void> => delay(mockServer.markTaskReady(taskId)),

  // Execution commands
  startStory: (storyId: string): Promise<StoryExecution> => delay(mockServer.startStory(storyId)),
  startTask: (taskId: string): Promise<void> => delay(mockServer.startTask(taskId)),
  cancelExecution: (executionId: string): Promise<void> => delay(mockServer.cancelExecution(executionId)),
  retryExecution: (executionId: string): Promise<void> => delay(mockServer.retryExecution(executionId)),

  // Decisions
  submitDecision: (humanRequestId: string, input: DecisionInput): Promise<Decision> =>
    delay(mockServer.submitDecision(humanRequestId, input)),

  // Notifications
  dismissNotification: (notificationId: string): Promise<void> => delay(mockServer.dismissNotification(notificationId)),
};
