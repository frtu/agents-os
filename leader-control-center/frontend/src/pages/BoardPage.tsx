import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import type { InitiativeSummary } from "@/types/domain";
import { AppShell } from "@/components/layout/AppShell";
import { InitiativeBoard } from "@/features/board/InitiativeBoard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useInitiatives } from "@/hooks/queries";
import { useCreateInitiative, useReorderInitiatives } from "@/hooks/mutations";

export function BoardPage() {
  const { data: summaries, isLoading } = useInitiatives();
  const createInitiative = useCreateInitiative();
  const reorder = useReorderInitiatives();

  // Drag-to-reorder state. `localOrder` holds an optimistic preview while a drop
  // is in flight; it resets to server truth whenever fresh data arrives.
  const [localOrder, setLocalOrder] = useState<InitiativeSummary[] | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);
  useEffect(() => setLocalOrder(null), [summaries]);
  const list = localOrder ?? summaries ?? [];

  const handleDrop = (dropIndex: number) => {
    if (dragIndex === null || dragIndex === dropIndex) return;
    const next = [...list];
    const [moved] = next.splice(dragIndex, 1);
    next.splice(dropIndex, 0, moved);
    setLocalOrder(next);
    reorder.mutate(next.map((s) => s.initiative.id));
    setDragIndex(null);
    setOverIndex(null);
  };

  // Create panel.
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const submitCreate = () => {
    if (!title.trim()) return;
    createInitiative.mutate(
      { title: title.trim(), description: description.trim() },
      {
        onSuccess: () => {
          setTitle("");
          setDescription("");
          setCreating(false);
        },
      },
    );
  };

  return (
    <AppShell title="Board">
      <ScrollArea className="h-full p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-muted-foreground">Initiatives</h2>
          <Button size="sm" onClick={() => setCreating((v) => !v)}>
            <Plus className="h-3.5 w-3.5" />
            New Initiative
          </Button>
        </div>

        {creating && (
          <div className="mb-6 flex flex-col gap-3 rounded-lg border border-border bg-card/40 p-4">
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Initiative title"
              className="rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              rows={2}
              className="resize-none rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            />
            <div className="flex items-center gap-2">
              <Button size="sm" onClick={submitCreate} disabled={!title.trim() || createInitiative.isPending}>
                Create
              </Button>
              <Button size="sm" variant="outline" onClick={() => setCreating(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        <div className="flex flex-col gap-6">
          {isLoading &&
            Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
          {list.map((summary, i) => (
            <InitiativeBoard
              key={summary.initiative.id}
              summary={summary}
              isDragging={dragIndex === i}
              isOver={overIndex === i && dragIndex !== null && dragIndex !== i}
              onDragStart={() => setDragIndex(i)}
              onDragOver={(e) => {
                e.preventDefault();
                if (overIndex !== i) setOverIndex(i);
              }}
              onDrop={() => handleDrop(i)}
              onDragEnd={() => {
                setDragIndex(null);
                setOverIndex(null);
              }}
            />
          ))}
          {summaries && summaries.length === 0 && !creating && (
            <div className="py-20 text-center text-sm text-muted-foreground">No initiatives yet.</div>
          )}
        </div>
      </ScrollArea>
    </AppShell>
  );
}
