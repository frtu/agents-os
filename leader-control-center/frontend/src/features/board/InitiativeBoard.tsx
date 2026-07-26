import { ChevronDown, ChevronRight, AlertCircle } from "lucide-react";
import type { BoardColumn as ColumnKey, InitiativeBoardView } from "@/types/domain";
import { BoardColumn } from "@/features/board/BoardColumn";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

const ORDER: ColumnKey[] = ["Todo", "Ready", "Running", "Blocked", "Completed"];

export function InitiativeBoard({ board }: { board: InitiativeBoardView }) {
  const collapsed = useUiStore((s) => s.collapsedInitiatives[board.initiative.id] ?? false);
  const toggle = useUiStore((s) => s.toggleInitiative);
  const total = ORDER.reduce((n, c) => n + board.columns[c].length, 0);

  return (
    <section className="rounded-lg border border-border bg-card/40">
      <button
        onClick={() => toggle(board.initiative.id)}
        className="flex w-full items-center gap-2 px-4 py-3 text-left"
      >
        {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        <span className="font-semibold">{board.initiative.title}</span>
        <span className="text-xs text-muted-foreground">{total} stories</span>
        {board.openHumanRequests > 0 && (
          <span className="ml-auto inline-flex items-center gap-1 text-xs text-status-blocked">
            <AlertCircle className="h-3.5 w-3.5" />
            {board.openHumanRequests}
          </span>
        )}
      </button>
      <div className={cn("overflow-x-auto scrollbar-thin", collapsed && "hidden")}>
        <div className="flex gap-4 p-4 pt-0">
          {ORDER.map((column) => (
            <BoardColumn key={column} column={column} cards={board.columns[column]} />
          ))}
        </div>
      </div>
    </section>
  );
}
