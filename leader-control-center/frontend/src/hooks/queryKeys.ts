export const qk = {
  initiatives: ["initiatives"] as const,
  board: (initiativeId: string) => ["board", initiativeId] as const,
  attention: ["attention"] as const,
  capabilities: ["capabilities"] as const,
  providers: ["providers"] as const,
  notifications: ["notifications"] as const,
  storyTasks: (storyId: string) => ["storyTasks", storyId] as const,
  execution: (executionId: string) => ["execution", executionId] as const,
  timeline: (executionId: string) => ["timeline", executionId] as const,
  decisions: (executionId: string) => ["decisions", executionId] as const,
  artifacts: (storyId: string) => ["artifacts", storyId] as const,
  artifact: (artifactId: string) => ["artifact", artifactId] as const,
};
