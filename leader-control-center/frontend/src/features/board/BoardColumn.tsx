import type { BoardColumn as ColumnKey, StoryCardView } from "@/types/domain";
import { StoryCard } from "@/features/board/StoryCard";
import { columnToStatusKey } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

const dotClass: Record<ReturnType<typeof columnToStatusKey>, string> = {
  todo: "bg-status-todo",
  ready: "bg-status-ready",
  running: "bg-status-running",
  waiting: "bg-status-waiting",
  blocked: "bg-status-blocked",
  completed: "bg-status-completed",
  failed: "bg-status-failed",
  cancelled: "bg-status-cancelled",
};

export function BoardColumn({ column, cards }: { column: ColumnKey; cards: StoryCardView[] }) {
  return (
    <div className="flex min-w-[240px] flex-1 flex-col">
      <div className="mb-2 flex items-center gap-2 px-1">
        <span className={cn("h-2 w-2 rounded-full", dotClass[columnToStatusKey(column)])} />
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{column}</span>
        <span className="text-xs text-muted-foreground">{cards.length}</span>
      </div>
      <div className="flex flex-col gap-2">
        {cards.map((card) => (
          <StoryCard key={card.story.id} card={card} />
        ))}
        {cards.length === 0 && (
          <div className="rounded-md border border-dashed border-border py-6 text-center text-xs text-muted-foreground">
            Empty
          </div>
        )}
      </div>
    </div>
  );
}
