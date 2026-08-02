import { useState } from "react";
import { Ban, Pencil, RotateCcw, X } from "lucide-react";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
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
  useDecisionHistory,
  useExecution,
  useStoryCard,
  useStoryTasks,
  useTimeline,
} from "@/hooks/queries";
import { useCancelExecution, useRetryExecution, useDeleteStory } from "@/hooks/mutations";

export function StoryDetailSheet() {
  const panel = useUiStore((s) => s.panel);
  const closePanel = useUiStore((s) => s.closePanel);
  const openEditStory = useUiStore((s) => s.openEditStory);
  const [confirmDiscard, setConfirmDiscard] = useState(false);
  const open = panel.kind === "story";
  const storyId = panel.kind === "story" ? panel.storyId : undefined;
  const panelExecutionId = panel.kind === "story" ? panel.executionId : undefined;

  const card = useStoryCard(storyId);
  const executionId = panelExecutionId ?? card?.execution?.id;
  const { data: tasks, isLoading: tasksLoading } = useStoryTasks(open ? storyId : undefined);
  const { data: execution } = useExecution(open ? executionId : undefined);
  const { data: timeline, isLoading: timelineLoading } = useTimeline(open ? executionId : undefined);
  const { data: decisions } = useDecisionHistory(open ? executionId : undefined);
  const { data: artifacts } = useArtifacts(open ? storyId : undefined);
  const { data: attention } = useAttention();

  const cancel = useCancelExecution();
  const retry = useRetryExecution();
  const discard = useDeleteStory();

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

      {card && (
        <div className="flex items-center gap-2 border-b border-border px-4 py-2">
          <Button size="sm" variant="outline" onClick={() => openEditStory(card.story)}>
            <Pencil className="h-3.5 w-3.5" />
            Edit
          </Button>
          {running && (
            <Button size="sm" variant="destructive" onClick={() => cancel.mutate(execution!.id)} disabled={cancel.isPending}>
              <Ban className="h-3.5 w-3.5" />
              Cancel
            </Button>
          )}
          {retryable && (
            <Button size="sm" variant="outline" onClick={() => retry.mutate(execution!.id)} disabled={retry.isPending}>
              <RotateCcw className="h-3.5 w-3.5" />
              Retry
            </Button>
          )}
          <Button size="sm" variant="outline" onClick={() => setConfirmDiscard(true)}>
            <X className="h-3.5 w-3.5" />
            Discard
          </Button>
        </div>
      )}

      <Dialog open={confirmDiscard} onClose={() => setConfirmDiscard(false)}>
        <h2 className="text-base font-semibold">Discard story?</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          "{card?.story.title}" will be removed from the board. This can't be undone here.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={() => setConfirmDiscard(false)}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={() =>
              storyId &&
              discard.mutate(storyId, {
                onSuccess: () => {
                  setConfirmDiscard(false);
                  closePanel();
                },
              })
            }
            disabled={discard.isPending}
          >
            Discard
          </Button>
        </div>
      </Dialog>

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
