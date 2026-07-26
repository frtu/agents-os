import { useMemo } from "react";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { ExecutionStatusBadge } from "@/components/ui/status-badge";
import { useBoards, useExecution, useStoryTasks } from "@/hooks/queries";
import { useStartTask } from "@/hooks/mutations";
import { useUiStore } from "@/store/ui";

export function TaskDetailSheet() {
  const panel = useUiStore((s) => s.panel);
  const closePanel = useUiStore((s) => s.closePanel);
  const open = panel.kind === "task";
  const taskId = panel.kind === "task" ? panel.taskId : undefined;
  const storyId = panel.kind === "task" ? panel.storyId : undefined;

  const { data: boards } = useBoards();
  const executionId = useMemo(() => {
    if (!boards || !storyId) return undefined;
    for (const b of boards) {
      for (const col of Object.values(b.columns)) {
        const found = col.find((c) => c.story.id === storyId);
        if (found) return found.execution?.id;
      }
    }
    return undefined;
  }, [boards, storyId]);

  const { data: tasks } = useStoryTasks(open ? storyId : undefined);
  const { data: execution } = useExecution(open ? executionId : undefined);
  const startTask = useStartTask(storyId ?? "");

  const task = tasks?.find((t) => t.id === taskId);
  const te = execution?.taskExecutions.find((x) => x.taskId === taskId);

  return (
    <Sheet open={open} onClose={closePanel} className="max-w-lg">
      <SheetHeader
        title={
          <span className="flex items-center gap-2">
            {task?.name ?? "Task"}
            {te && <ExecutionStatusBadge status={te.status} />}
          </span>
        }
        description={task ? `${task.planningMode} · ${task.status}` : undefined}
        onClose={closePanel}
      />
      <ScrollArea className="min-h-0 flex-1 p-4">
        {task?.goal && (
          <div className="mb-4">
            <div className="text-xs font-semibold uppercase text-muted-foreground">Goal</div>
            <p className="mt-1 text-sm">{task.goal}</p>
          </div>
        )}

        {task && !te && task.status !== "Cancelled" && (
          <Button size="sm" className="mb-4" onClick={() => startTask.mutate(task.id)} disabled={startTask.isPending}>
            Start task
          </Button>
        )}

        {te ? (
          <div className="flex flex-col gap-3">
            {te.waitingReason && (
              <div className="rounded-md border border-status-waiting/40 bg-status-waiting/10 p-2 text-xs">
                {te.waitingReason}
              </div>
            )}
            {te.capabilityExecutions.map((ce) => (
              <div key={ce.id} className="rounded-md border border-border p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{ce.capabilityName}</span>
                  <Badge variant="secondary">{ce.strategy}</Badge>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">{ce.status}</div>
                <Separator className="my-2" />
                <div className="flex flex-col gap-1">
                  {ce.providerExecutions.map((pe) => (
                    <div key={pe.id} className="flex items-center justify-between text-xs">
                      <span>
                        {pe.providerName}
                        {pe.attempt > 1 && <span className="text-muted-foreground"> · attempt {pe.attempt}</span>}
                      </span>
                      <Badge variant="outline">{pe.status}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="py-6 text-center text-sm text-muted-foreground">Task not yet executing.</p>
        )}
      </ScrollArea>
    </Sheet>
  );
}
