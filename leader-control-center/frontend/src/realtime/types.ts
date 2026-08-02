/** Server → client realtime messages. Mirrors specs/api/realtime.md. */
export type RealtimeMessageType =
  | "StoryUpdated"
  | "ExecutionUpdated"
  | "TimelineUpdated"
  | "DecisionRequested"
  | "DecisionApplied"
  | "ArtifactProduced"
  | "AttentionUpdated"
  | "NotificationCreated"
  | "WorkflowDefinitionUpdated";

export interface RealtimeMessage {
  type: RealtimeMessageType;
  aggregateId: string;
  sequence: number;
  payload?: Record<string, unknown>;
}

export interface RealtimeConnection {
  start(): void;
  stop(): void;
  subscribe(listener: (msg: RealtimeMessage) => void): () => void;
}
