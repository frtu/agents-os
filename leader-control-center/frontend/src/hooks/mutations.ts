import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api";
import type { DecisionInput } from "@/api/types";
import { qk } from "@/hooks/queryKeys";

export function useMarkTaskReady(storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => api.markTaskReady(taskId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.storyTasks(storyId) });
      qc.invalidateQueries({ queryKey: qk.boards });
    },
  });
}

export function useStartStory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (storyId: string) => api.startStory(storyId),
    onSuccess: (exec) => {
      qc.invalidateQueries({ queryKey: qk.boards });
      qc.invalidateQueries({ queryKey: qk.execution(exec.id) });
      qc.invalidateQueries({ queryKey: qk.timeline(exec.id) });
    },
  });
}

export function useStartTask(storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => api.startTask(taskId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.storyTasks(storyId) });
      qc.invalidateQueries({ queryKey: qk.boards });
    },
  });
}

export function useCancelExecution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (executionId: string) => api.cancelExecution(executionId),
    onSuccess: (_r, executionId) => {
      qc.invalidateQueries({ queryKey: qk.boards });
      qc.invalidateQueries({ queryKey: qk.execution(executionId) });
      qc.invalidateQueries({ queryKey: qk.attention });
    },
  });
}

export function useRetryExecution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (executionId: string) => api.retryExecution(executionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.boards });
    },
  });
}

export function useSubmitDecision(executionId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ humanRequestId, input }: { humanRequestId: string; input: DecisionInput }) =>
      api.submitDecision(humanRequestId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.attention });
      qc.invalidateQueries({ queryKey: qk.boards });
      if (executionId) {
        qc.invalidateQueries({ queryKey: qk.execution(executionId) });
        qc.invalidateQueries({ queryKey: qk.timeline(executionId) });
        qc.invalidateQueries({ queryKey: qk.decisions(executionId) });
      }
    },
  });
}

export function useDismissNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissNotification(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.notifications }),
  });
}
