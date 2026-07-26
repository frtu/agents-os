import type { Task, TaskExecution } from "@/types/domain";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExecutionStatusBadge } from "@/components/ui/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useUiStore } from "@/store/ui";
import { useMarkTaskReady } from "@/hooks/mutations";

export function TaskList({
  storyId,
  tasks,
  taskExecutions,
  isLoading,
}: {
  storyId: string;
  tasks?: Task[];
  taskExecutions?: TaskExecution[];
  isLoading?: boolean;
}) {
  const openTask = useUiStore((s) => s.openTask);
  const markReady = useMarkTaskReady(storyId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!tasks || tasks.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No tasks.</p>;
  }

  const execByTask = new Map((taskExecutions ?? []).map((te) => [te.taskId, te]));

  return (
    <div className="flex flex-col gap-2">
      {tasks.map((task) => {
        const te = execByTask.get(task.id);
        return (
          <div
            key={task.id}
            onClick={() => openTask(task.id, storyId)}
            className="flex cursor-pointer items-center justify-between gap-3 rounded-md border border-border bg-card p-3 hover:border-primary/50"
          >
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{task.name}</div>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="secondary">{task.planningMode}</Badge>
                {te?.waitingReason && <span>{te.waitingReason}</span>}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {te ? (
                <ExecutionStatusBadge status={te.status} />
              ) : task.status === "Draft" ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    markReady.mutate(task.id);
                  }}
                  disabled={markReady.isPending}
                >
                  Mark ready
                </Button>
              ) : (
                <Badge variant="outline">{task.status}</Badge>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
