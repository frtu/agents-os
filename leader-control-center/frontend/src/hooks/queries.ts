import { useQuery } from "@tanstack/react-query";
import { api } from "@/api";
import { qk } from "@/hooks/queryKeys";

export function useBoards() {
  return useQuery({ queryKey: qk.boards, queryFn: () => api.getBoards() });
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

export function useDecisions(executionId: string | undefined) {
  return useQuery({
    queryKey: qk.decisions(executionId ?? ""),
    queryFn: () => api.getDecisions(executionId!),
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
