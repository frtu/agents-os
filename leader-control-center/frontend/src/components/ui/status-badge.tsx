import { cn } from "@/lib/utils";
import type { BoardColumn, StoryExecutionStatus, TaskExecutionStatus } from "@/types/domain";

type StatusKey =
  | "todo"
  | "ready"
  | "running"
  | "waiting"
  | "blocked"
  | "completed"
  | "failed"
  | "cancelled";

// Full literal class names so Tailwind does not purge them.
const styles: Record<StatusKey, string> = {
  todo: "bg-status-todo/15 text-status-todo",
  ready: "bg-status-ready/15 text-status-ready",
  running: "bg-status-running/15 text-status-running",
  waiting: "bg-status-waiting/20 text-status-waiting",
  blocked: "bg-status-blocked/15 text-status-blocked",
  completed: "bg-status-completed/15 text-status-completed",
  failed: "bg-status-failed/15 text-status-failed",
  cancelled: "bg-status-cancelled/15 text-status-cancelled",
};

const dot: Record<StatusKey, string> = {
  todo: "bg-status-todo",
  ready: "bg-status-ready",
  running: "bg-status-running",
  waiting: "bg-status-waiting",
  blocked: "bg-status-blocked",
  completed: "bg-status-completed",
  failed: "bg-status-failed",
  cancelled: "bg-status-cancelled",
};

const columnKey: Record<BoardColumn, StatusKey> = {
  Todo: "todo",
  Ready: "ready",
  Running: "running",
  Blocked: "blocked",
  Completed: "completed",
};

const execKey: Record<StoryExecutionStatus | TaskExecutionStatus, StatusKey> = {
  Created: "todo",
  Running: "running",
  Waiting: "waiting",
  WaitingDecision: "waiting",
  Completed: "completed",
  Cancelled: "cancelled",
  Failed: "failed",
};

export function columnToStatusKey(column: BoardColumn): StatusKey {
  return columnKey[column];
}

export function StatusBadge({
  status,
  pulse,
  className,
}: {
  status: StatusKey;
  pulse?: boolean;
  className?: string;
}) {
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium",
        styles[status],
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", dot[status], pulse && "animate-pulse-ring")} />
      {label}
    </span>
  );
}

export function ColumnBadge({ column, className }: { column: BoardColumn; className?: string }) {
  const key = columnKey[column];
  return <StatusBadge status={key} pulse={key === "running"} className={className} />;
}

export function ExecutionStatusBadge({
  status,
  className,
}: {
  status: StoryExecutionStatus | TaskExecutionStatus;
  className?: string;
}) {
  const key = execKey[status];
  return <StatusBadge status={key} pulse={key === "running"} className={className} />;
}
