import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api";
import type { DecisionInput } from "@/api/types";
import type {
  CreateStoryInput,
  CreateWorkflowDefinitionInput,
  UpdateWorkflowDefinitionInput,
} from "@/types/domain";
import { qk } from "@/hooks/queryKeys";

export function useCreateInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { title: string; description?: string; workflowDefinitionId?: string }) =>
      api.createInitiative(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.initiatives }),
  });
}

export function useDeleteInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (initiativeId: string) => api.deleteInitiative(initiativeId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.initiatives });
      // Orphaned stories move to Misc, so any open board may have changed.
      qc.invalidateQueries({ queryKey: ["board"] });
    },
  });
}

export function useReorderInitiatives() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (initiativeIds: string[]) => api.reorderInitiatives(initiativeIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.initiatives }),
  });
}

export function useCreateStory(initiativeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateStoryInput) => api.createStory(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.board(initiativeId) });
      qc.invalidateQueries({ queryKey: qk.initiatives });
    },
  });
}

export function useDraftStory() {
  return useMutation({
    mutationFn: (input: { initiativeId: string; message: string }) => api.draftStory(input),
  });
}

export function useMarkTaskReady(storyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => api.markTaskReady(taskId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.storyTasks(storyId) });
      qc.invalidateQueries({ queryKey: qk.initiatives });
      qc.invalidateQueries({ queryKey: ["board"] });
    },
  });
}

export function useStartStory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (storyId: string) => api.startStory(storyId),
    onSuccess: (exec) => {
      qc.invalidateQueries({ queryKey: qk.initiatives });
      qc.invalidateQueries({ queryKey: ["board"] });
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
      qc.invalidateQueries({ queryKey: qk.initiatives });
      qc.invalidateQueries({ queryKey: ["board"] });
    },
  });
}

export function useCancelExecution() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (executionId: string) => api.cancelExecution(executionId),
    onSuccess: (_r, executionId) => {
      qc.invalidateQueries({ queryKey: qk.initiatives });
      qc.invalidateQueries({ queryKey: ["board"] });
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
      qc.invalidateQueries({ queryKey: qk.initiatives });
      qc.invalidateQueries({ queryKey: ["board"] });
    },
  });
}

export function useSubmitDecision(executionId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ decisionId, input }: { decisionId: string; input: DecisionInput }) =>
      api.submitDecision(executionId!, decisionId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.attention });
      qc.invalidateQueries({ queryKey: qk.initiatives });
      qc.invalidateQueries({ queryKey: ["board"] });
      if (executionId) {
        qc.invalidateQueries({ queryKey: qk.execution(executionId) });
        qc.invalidateQueries({ queryKey: qk.timeline(executionId) });
        qc.invalidateQueries({ queryKey: qk.decisions(executionId) });
      }
    },
  });
}

export function useCreateWorkflowDefinition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateWorkflowDefinitionInput) => api.createWorkflowDefinition(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.workflowDefinitions }),
  });
}

export function useUpdateWorkflowDefinition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ wdId, input }: { wdId: string; input: UpdateWorkflowDefinitionInput }) =>
      api.updateWorkflowDefinition(wdId, input),
    onSuccess: (_r, { wdId }) => {
      qc.invalidateQueries({ queryKey: qk.workflowDefinitions });
      qc.invalidateQueries({ queryKey: qk.workflowDefinition(wdId) });
    },
  });
}

export function useDeleteWorkflowDefinition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (wdId: string) => api.deleteWorkflowDefinition(wdId),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.workflowDefinitions }),
  });
}

export function useOpenNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.openNotification(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.notifications }),
  });
}

export function useAckNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.ackNotification(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.notifications }),
  });
}

export function useCloseNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.closeNotification(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.notifications }),
  });
}
