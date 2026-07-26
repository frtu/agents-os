import { useMemo } from "react";
import { Ban, RotateCcw } from "lucide-react";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ExecutionStatusBadge } from "@/components/ui/status-badge";
import { TaskList } from "@/features/story/TaskList";
import { Timeline } from "@/features/story/Timeline";
import { DecisionList } from "@/features/story/DecisionList";
import { ArtifactList } from "@/features/artifacts/ArtifactList";
import { HumanRequestCard } from "@/features/decisions/HumanRequestCard";
import { useUiStore } from "@/store/ui";
import {
  useArtifacts,
  useAttention,
  useBoards,
  useDecisions,
  useExecution,
  useStoryTasks,
  useTimeline,
} from "@/hooks/queries";
import { useCancelExecution, useRetryExecution } from "@/hooks/mutations";

export function StoryDetailSheet() {
  const panel = useUiStore((s) => s.panel);
  const closePanel = useUiStore((s) => s.closePanel);
  const open = panel.kind === "story";
  const storyId = panel.kind === "story" ? panel.storyId : undefined;

  const { data: boards } = useBoards();
  const card = useMemo(() => {
    if (!boards || !storyId) return undefined;
    for (const b of boards) {
      for (const col of Object.values(b.columns)) {
        const found = col.find((c) => c.story.id === storyId);
        if (found) return found;
      }
    }
    return undefined;
  }, [boards, storyId]);

  const executionId = card?.execution?.id;
  const { data: tasks, isLoading: tasksLoading } = useStoryTasks(open ? storyId : undefined);
  const { data: execution } = useExecution(open ? executionId : undefined);
  const { data: timeline, isLoading: timelineLoading } = useTimeline(open ? executionId : undefined);
  const { data: decisions } = useDecisions(open ? executionId : undefined);
  const { data: artifacts } = useArtifacts(open ? storyId : undefined);
  const { data: attention } = useAttention();

  const cancel = useCancelExecution();
  const retry = useRetryExecution();

  const openRequests = (attention ?? []).filter((r) => r.executionId === executionId);
  const running = execution?.status === "Running" || execution?.status === "Waiting";
  const retryable = execution?.status === "Failed" || execution?.status === "Cancelled";

  return (
    <Sheet open={open} onClose={closePanel}>
      <SheetHeader
        title={
          <span className="flex items-center gap-2">
            {card?.story.title ?? "Story"}
            {execution && <ExecutionStatusBadge status={execution.status} />}
          </span>
        }
        description={card?.story.description}
        onClose={closePanel}
      />

      {execution && (
        <div className="flex items-center gap-2 border-b border-border px-4 py-2">
          {running && (
            <Button size="sm" variant="destructive" onClick={() => cancel.mutate(execution.id)} disabled={cancel.isPending}>
              <Ban className="h-3.5 w-3.5" />
              Cancel
            </Button>
          )}
          {retryable && (
            <Button size="sm" variant="outline" onClick={() => retry.mutate(execution.id)} disabled={retry.isPending}>
              <RotateCcw className="h-3.5 w-3.5" />
              Retry
            </Button>
          )}
        </div>
      )}

      <ScrollArea className="min-h-0 flex-1 p-4">
        {openRequests.length > 0 && (
          <div className="mb-4 flex flex-col gap-3">
            {openRequests.map((r) => (
              <HumanRequestCard key={r.id} request={r} />
            ))}
          </div>
        )}

        <Tabs defaultValue="tasks">
          <TabsList>
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="artifacts">Artifacts</TabsTrigger>
            <TabsTrigger value="decisions">Decisions</TabsTrigger>
          </TabsList>

          <TabsContent value="tasks">
            <TaskList
              storyId={storyId!}
              tasks={tasks}
              taskExecutions={execution?.taskExecutions}
              isLoading={tasksLoading}
            />
          </TabsContent>
          <TabsContent value="timeline">
            <Timeline events={timeline} isLoading={timelineLoading} />
          </TabsContent>
          <TabsContent value="artifacts">
            <ArtifactList artifacts={artifacts} />
          </TabsContent>
          <TabsContent value="decisions">
            <DecisionList decisions={decisions} />
          </TabsContent>
        </Tabs>
      </ScrollArea>
    </Sheet>
  );
}
