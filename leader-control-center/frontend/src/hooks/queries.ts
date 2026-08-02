import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api";
import { qk } from "@/hooks/queryKeys";
import type { InitiativeBoardView, StoryCardView } from "@/types/domain";

export function useInitiatives() {
  return useQuery({ queryKey: qk.initiatives, queryFn: () => api.getInitiatives() });
}

export function useInitiativeBoard(initiativeId: string, enabled: boolean) {
  return useQuery({
    queryKey: qk.board(initiativeId),
    queryFn: () => api.getBoard(initiativeId),
    enabled,
  });
}

/**
 * Finds a story's card among the per-initiative boards already in the query
 * cache. A board is loaded (and cached) before any of its cards can be clicked,
 * so the detail panels can resolve their story without a dedicated endpoint.
 * Subscribes to the initiatives list so it re-renders when the same realtime
 * events that refresh boards fire.
 */
export function useStoryCard(storyId: string | undefined): StoryCardView | undefined {
  const qc = useQueryClient();
  useInitiatives();
  if (!storyId) return undefined;
  for (const [, board] of qc.getQueriesData<InitiativeBoardView>({ queryKey: ["board"] })) {
    if (!board) continue;
    for (const col of Object.values(board.columns)) {
      const found = col.find((c) => c.story.id === storyId);
      if (found) return found;
    }
  }
  return undefined;
}

export function useAttention() {
  return useQuery({ queryKey: qk.attention, queryFn: () => api.getAttention() });
}

export function useCapabilities() {
  return useQuery({ queryKey: qk.capabilities, queryFn: () => api.getCapabilities() });
}

export function useProviders() {
  return useQuery({ queryKey: qk.providers, queryFn: () => api.getProviders() });
}

export function useNotifications() {
  return useQuery({ queryKey: qk.notifications, queryFn: () => api.getNotifications() });
}

export function useWorkflowDefinitions() {
  return useQuery({
    queryKey: qk.workflowDefinitions,
    queryFn: () => api.getWorkflowDefinitions(),
  });
}

export function useWorkflowDefinition(wdId: string | undefined) {
  return useQuery({
    queryKey: qk.workflowDefinition(wdId ?? ""),
    queryFn: () => api.getWorkflowDefinition(wdId!),
    enabled: !!wdId,
  });
}

export function useStoryTasks(storyId: string | undefined) {
  return useQuery({
    queryKey: qk.storyTasks(storyId ?? ""),
    queryFn: () => api.getStoryTasks(storyId!),
    enabled: !!storyId,
  });
}

export function useExecution(executionId: string | undefined) {
  return useQuery({
    queryKey: qk.execution(executionId ?? ""),
    queryFn: () => api.getExecution(executionId!),
    enabled: !!executionId,
  });
}

export function useTimeline(executionId: string | undefined) {
  return useQuery({
    queryKey: qk.timeline(executionId ?? ""),
    queryFn: () => api.getTimeline(executionId!),
    enabled: !!executionId,
  });
}

export function useDecisionHistory(executionId: string | undefined) {
  return useQuery({
    queryKey: qk.decisions(executionId ?? ""),
    queryFn: () => api.getDecisionHistory(executionId!),
    enabled: !!executionId,
  });
}

export function useArtifacts(storyId: string | undefined) {
  return useQuery({
    queryKey: qk.artifacts(storyId ?? ""),
    queryFn: () => api.getArtifacts(storyId!),
    enabled: !!storyId,
  });
}

export function useArtifact(artifactId: string | undefined) {
  return useQuery({
    queryKey: qk.artifact(artifactId ?? ""),
    queryFn: () => api.getArtifact(artifactId!),
    enabled: !!artifactId,
  });
}
