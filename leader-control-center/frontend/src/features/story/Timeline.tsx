import { Activity, FileText, GitBranch, MessageSquare } from "lucide-react";
import type { TimelineEvent, TimelineEventCategory } from "@/types/domain";
import { formatTime } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const icon: Record<TimelineEventCategory, React.ComponentType<{ className?: string }>> = {
  Runtime: Activity,
  Decision: MessageSquare,
  Artifact: FileText,
  System: GitBranch,
};

export function Timeline({ events, isLoading }: { events?: TimelineEvent[]; isLoading?: boolean }) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!events || events.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No events yet.</p>;
  }

  return (
    <ol className="relative ml-2 border-l border-border">
      {events.map((e) => {
        const Icon = icon[e.category];
        return (
          <li key={e.id} className="mb-4 ml-4">
            <span className="absolute -left-[9px] flex h-4 w-4 items-center justify-center rounded-full bg-background ring-1 ring-border">
              <Icon className="h-2.5 w-2.5 text-muted-foreground" />
            </span>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-sm font-medium">{e.type}</span>
              <span className="shrink-0 text-xs text-muted-foreground">{formatTime(e.occurredAt)}</span>
            </div>
            {e.detail && <p className="text-xs text-muted-foreground">{e.detail}</p>}
          </li>
        );
      })}
    </ol>
  );
}
