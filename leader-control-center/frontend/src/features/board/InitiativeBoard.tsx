import { useState } from "react";
import { ChevronDown, ChevronRight, AlertCircle, GripVertical, Pencil, Trash2 } from "lucide-react";
import type { BoardColumn as ColumnKey, InitiativeSummary } from "@/types/domain";
import { BoardColumn } from "@/features/board/BoardColumn";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";
import { useInitiativeBoard, useWorkflowDefinitions } from "@/hooks/queries";
import { useDeleteInitiative, useUpdateInitiative } from "@/hooks/mutations";

const inputClass =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary";

const ORDER: ColumnKey[] = ["Todo", "Ready", "Running", "Blocked", "Completed"];

// Stable id of the default initiative that hosts orphaned stories; not deletable.
const MISC_INITIATIVE_ID = "init_misc";

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
  const deleteInitiative = useDeleteInitiative();
  const updateInitiative = useUpdateInitiative();
  const { data: workflowDefinitions } = useWorkflowDefinitions();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editTitle, setEditTitle] = useState(initiative.title);
  const [editDescription, setEditDescription] = useState(initiative.description);
  const [editWorkflowId, setEditWorkflowId] = useState(initiative.workflowDefinitionId ?? "");
  const [editError, setEditError] = useState<string | null>(null);
  const isMisc = initiative.id === MISC_INITIATIVE_ID;

  const openEdit = () => {
    setEditTitle(initiative.title);
    setEditDescription(initiative.description);
    setEditWorkflowId(initiative.workflowDefinitionId ?? "");
    setEditError(null);
    setEditOpen(true);
  };

  const submitEdit = () => {
    if (!editTitle.trim()) return;
    setEditError(null);
    updateInitiative.mutate(
      {
        initiativeId: initiative.id,
        input: {
          title: editTitle.trim(),
          description: editDescription.trim(),
          workflowDefinitionId: editWorkflowId || undefined,
        },
      },
      {
        onSuccess: () => setEditOpen(false),
        onError: (e) => setEditError(e instanceof Error ? e.message : "Failed to save"),
      },
    );
  };

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
        {!isMisc && (
          <>
            <button
              onClick={openEdit}
              aria-label={`Edit initiative ${initiative.title}`}
              className="ml-1 rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <Pencil className="h-4 w-4" />
            </button>
            <button
              onClick={() => setConfirmOpen(true)}
              aria-label={`Delete initiative ${initiative.title}`}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </>
        )}
      </div>

      <Dialog open={editOpen} onClose={() => setEditOpen(false)}>
        <div className="text-base font-semibold">Edit initiative</div>
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Title</span>
            <input
              autoFocus
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="Initiative title"
              className={inputClass}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Description</span>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Description (optional)"
              rows={2}
              className={`${inputClass} resize-none`}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">
              Workflow definition (optional)
            </span>
            <select
              value={editWorkflowId}
              onChange={(e) => setEditWorkflowId(e.target.value)}
              className={inputClass}
            >
              <option value="">None</option>
              {workflowDefinitions?.map((wd) => (
                <option key={wd.id} value={wd.id}>
                  {wd.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {editError && <p className="mt-3 text-sm text-status-blocked">{editError}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => setEditOpen(false)}>
            Cancel
          </Button>
          <Button
            size="sm"
            disabled={!editTitle.trim() || updateInitiative.isPending}
            onClick={submitEdit}
          >
            Save changes
          </Button>
        </div>
      </Dialog>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <div className="text-base font-semibold">Delete initiative</div>
        <p className="mt-2 text-sm text-muted-foreground">
          Delete <span className="font-medium text-foreground">{initiative.title}</span>? Its stories
          will be moved to the <span className="font-medium text-foreground">Misc</span> initiative.
          This can&apos;t be undone.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => setConfirmOpen(false)}>
            Cancel
          </Button>
          <Button
            size="sm"
            variant="destructive"
            disabled={deleteInitiative.isPending}
            onClick={() =>
              deleteInitiative.mutate(initiative.id, { onSuccess: () => setConfirmOpen(false) })
            }
          >
            Delete
          </Button>
        </div>
      </Dialog>

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
