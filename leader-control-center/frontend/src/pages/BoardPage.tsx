import { AppShell } from "@/components/layout/AppShell";
import { InitiativeBoard } from "@/features/board/InitiativeBoard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { useBoards } from "@/hooks/queries";

export function BoardPage() {
  const { data: boards, isLoading } = useBoards();

  return (
    <AppShell title="Board">
      <ScrollArea className="h-full p-6">
        <div className="flex flex-col gap-6">
          {isLoading &&
            Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-48 w-full" />)}
          {boards?.map((board) => (
            <InitiativeBoard key={board.initiative.id} board={board} />
          ))}
          {boards && boards.length === 0 && (
            <div className="py-20 text-center text-sm text-muted-foreground">No initiatives yet.</div>
          )}
        </div>
      </ScrollArea>
    </AppShell>
  );
}
