import type {
  Artifact,
  Capability,
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

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

interface ProblemJson {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  instance?: string;
}

export class ApiError extends Error {
  status: number;
  problem?: ProblemJson;
  constructor(status: number, message: string, problem?: ProblemJson) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!res.ok) {
    let problem: ProblemJson | undefined;
    try {
      problem = (await res.json()) as ProblemJson;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, problem?.title ?? res.statusText, problem);
  }

  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return (await res.json()) as T;
}

const get = <T>(path: string) => request<T>(path, { method: "GET" });
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

/** Maps a DecisionKind to its REST endpoint segment + optional body. */
function decisionEndpoint(input: DecisionInput): { path: string; body?: unknown } {
  switch (input.decision) {
    case "Approve":
      return { path: "approve" };
    case "Reject":
      return { path: "reject", body: { comment: input.comment } };
    case "Clarify":
      return { path: "clarify", body: { message: input.comment } };
    case "Continue":
      return { path: "continue" };
    case "Abort":
      return { path: "abort" };
    case "Retry":
      return { path: "retry" };
    case "SelectOption":
      return { path: "select", body: { optionId: input.selectedOption } };
    case "Custom":
      return { path: "custom", body: { actionName: input.actionName, comment: input.comment } };
  }
}

export const httpClient: ApiClient = {
  // Queries
  getInitiatives: () => get<InitiativeSummary[]>("/initiatives"),
  getBoard: (initiativeId) => get<InitiativeBoardView>(`/initiatives/${initiativeId}/board`),
  getStoryTasks: (storyId) => get<Task[]>(`/stories/${storyId}/tasks`),
  getExecution: (executionId) => get<StoryExecution>(`/executions/${executionId}`),
  getTimeline: (storyExecutionId) => get<TimelineEvent[]>(`/executions/${storyExecutionId}/timeline`),
  getArtifacts: (storyId) => get<Artifact[]>(`/stories/${storyId}/artifacts`),
  getArtifact: (artifactId) => get<Artifact>(`/artifacts/${artifactId}`),
  getAttention: () => get<HumanRequest[]>("/attention"),
  getOpenDecisions: (executionId) => get<HumanRequest[]>(`/executions/${executionId}/decisions`),
  getDecisionHistory: (executionId) => get<Decision[]>(`/executions/${executionId}/decisions/history`),
  getCapabilities: () => get<Capability[]>("/capabilities"),
  getProviders: () => get<Provider[]>("/providers"),
  getNotifications: () => get<Notification[]>("/notifications"),

  // Planning commands
  createInitiative: (input) => post<Initiative>("/initiatives", input),
  reorderInitiatives: (initiativeIds) =>
    post<InitiativeSummary[]>("/initiatives/reorder", { initiativeIds }),
  deleteInitiative: (initiativeId) => post<void>(`/initiatives/${initiativeId}/delete`),
  createStory: (input) => post<Story>("/stories", input),
  draftStory: (input) => post<StoryDraft>("/stories/draft", input),
  markTaskReady: (taskId) => post<void>(`/tasks/${taskId}/ready`),

  // Execution commands
  startStory: (storyId) => post<StoryExecution>(`/stories/${storyId}/start`),
  startTask: (taskId) => post<void>(`/tasks/${taskId}/start`),
  cancelExecution: (executionId) => post<void>(`/executions/${executionId}/cancel`),
  retryExecution: (executionId) => post<void>(`/executions/${executionId}/retry`),

  // Decisions — resolve an execution's open decision-to-make
  submitDecision: (executionId, decisionId, input) => {
    const { path, body } = decisionEndpoint(input);
    return post<Decision>(`/executions/${executionId}/decisions/${decisionId}/${path}`, body);
  },

  // Notifications (lifecycle: UNREAD -> READ -> ACKED -> CLOSED)
  openNotification: (notificationId) => post<void>(`/notifications/${notificationId}/open`),
  ackNotification: (notificationId) => post<void>(`/notifications/${notificationId}/ack`),
  closeNotification: (notificationId) => post<void>(`/notifications/${notificationId}/close`),
};
