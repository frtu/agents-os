import { ChevronDown, ChevronRight, AlertCircle, GripVertical } from "lucide-react";
import type { BoardColumn as ColumnKey, InitiativeSummary } from "@/types/domain";
import { BoardColumn } from "@/features/board/BoardColumn";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";
import { useInitiativeBoard } from "@/hooks/queries";

const ORDER: ColumnKey[] = ["Todo", "Ready", "Running", "Blocked", "Completed"];

interface Props {
  summary: InitiativeSummary;
  isDragging: boolean;
  isOver: boolean;
  onDragStart: () => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: () => void;
  onDragEnd: () => void;
}

export function InitiativeBoard({
  summary,
  isDragging,
  isOver,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
}: Props) {
  const { initiative, epicId, storyCount, openHumanRequests } = summary;
  const expanded = useUiStore((s) => s.expandedInitiatives[initiative.id] ?? false);
  const toggle = useUiStore((s) => s.toggleInitiative);
  const { data: board, isLoading } = useInitiativeBoard(initiative.id, expanded);

  return (
    <section
      onDragOver={onDragOver}
      onDrop={onDrop}
      onDragEnd={onDragEnd}
      className={cn(
        "rounded-lg border border-border bg-card/40 transition-opacity",
        isDragging && "opacity-40",
        isOver && "border-primary ring-1 ring-primary",
      )}
    >
      <div className="flex items-center gap-1 px-2 py-3">
        <span
          draggable
          onDragStart={onDragStart}
          aria-label="Drag to reorder"
          className="cursor-grab px-1 text-muted-foreground hover:text-foreground active:cursor-grabbing"
        >
          <GripVertical className="h-4 w-4" />
        </span>
        <button
          onClick={() => toggle(initiative.id)}
          className="flex flex-1 items-center gap-2 text-left"
        >
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <span className="font-semibold">{initiative.title}</span>
          <span className="text-xs text-muted-foreground">{storyCount} stories</span>
          {openHumanRequests > 0 && (
            <span className="ml-auto inline-flex items-center gap-1 text-xs text-status-blocked">
              <AlertCircle className="h-3.5 w-3.5" />
              {openHumanRequests}
            </span>
          )}
        </button>
      </div>

      {expanded && (
        <div className="overflow-x-auto scrollbar-thin">
          {isLoading || !board ? (
            <div className="flex gap-4 p-4 pt-0">
              {ORDER.map((c) => (
                <Skeleton key={c} className="h-40 w-64 shrink-0" />
              ))}
            </div>
          ) : (
            <div className="flex gap-4 p-4 pt-0">
              {ORDER.map((column) => (
                <BoardColumn
                  key={column}
                  column={column}
                  cards={board.columns[column]}
                  initiativeId={initiative.id}
                  epicId={epicId}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
