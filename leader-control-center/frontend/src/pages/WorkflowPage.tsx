import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { WorkflowDefinition } from "@/types/domain";
import { AppShell } from "@/components/layout/AppShell";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { useWorkflowDefinitions } from "@/hooks/queries";
import {
  useCreateWorkflowDefinition,
  useUpdateWorkflowDefinition,
  useDeleteWorkflowDefinition,
} from "@/hooks/mutations";

const inputClass =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary";

const SAMPLE_SCHEMA = JSON.stringify(
  { type: "object", required: [], properties: {} },
  null,
  2,
);

interface EditorState {
  id: string | null; // null = creating a new definition
  name: string;
  inputText: string;
  definition: string;
}

const emptyEditor: EditorState = {
  id: null,
  name: "",
  inputText: SAMPLE_SCHEMA,
  definition: "",
};

function editorFrom(wd: WorkflowDefinition): EditorState {
  return {
    id: wd.id,
    name: wd.name,
    inputText: JSON.stringify(wd.input ?? {}, null, 2),
    definition: wd.definition,
  };
}

export function WorkflowPage() {
  const { data: definitions, isLoading } = useWorkflowDefinitions();
  const createWd = useCreateWorkflowDefinition();
  const updateWd = useUpdateWorkflowDefinition();
  const deleteWd = useDeleteWorkflowDefinition();

  const [editor, setEditor] = useState<EditorState | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<WorkflowDefinition | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    setJsonError(null);
    setSaveError(null);
  }, [editor]);

  const startCreate = () => setEditor({ ...emptyEditor });
  const startEdit = (wd: WorkflowDefinition) => setEditor(editorFrom(wd));

  const save = () => {
    if (!editor || !editor.name.trim()) return;
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(editor.inputText || "{}");
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : "Invalid JSON");
      return;
    }
    const payload = {
      name: editor.name.trim(),
      input: parsed,
      definition: editor.definition,
    };
    const onError = (e: unknown) =>
      setSaveError(e instanceof Error ? e.message : "Failed to save");
    if (editor.id) {
      updateWd.mutate(
        { wdId: editor.id, input: payload },
        { onSuccess: () => setEditor(null), onError },
      );
    } else {
      createWd.mutate(payload, { onSuccess: () => setEditor(null), onError });
    }
  };

  const doDelete = () => {
    if (!confirmDelete) return;
    setDeleteError(null);
    deleteWd.mutate(confirmDelete.id, {
      onSuccess: () => {
        if (editor?.id === confirmDelete.id) setEditor(null);
        setConfirmDelete(null);
      },
      onError: (e) =>
        setDeleteError(e instanceof Error ? e.message : "Failed to delete"),
    });
  };

  const saving = createWd.isPending || updateWd.isPending;

  return (
    <AppShell title="Workflow">
      <div className="flex h-full">
        {/* List */}
        <div className="flex w-72 shrink-0 flex-col border-r border-border">
          <div className="flex items-center justify-between px-4 py-3">
            <h2 className="text-sm font-semibold text-muted-foreground">Definitions</h2>
            <Button size="sm" onClick={startCreate}>
              <Plus className="h-3.5 w-3.5" />
              New
            </Button>
          </div>
          <ScrollArea className="min-h-0 flex-1 px-2 pb-2">
            <div className="flex flex-col gap-1">
              {isLoading &&
                Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              {definitions?.map((wd) => (
                <button
                  key={wd.id}
                  onClick={() => startEdit(wd)}
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors",
                    editor?.id === wd.id
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                  )}
                >
                  <span className="min-w-0 flex-1 truncate font-medium">{wd.name}</span>
                  <span
                    role="button"
                    tabIndex={0}
                    aria-label={`Delete ${wd.name}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteError(null);
                      setConfirmDelete(wd);
                    }}
                    className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </span>
                </button>
              ))}
              {definitions && definitions.length === 0 && (
                <p className="px-3 py-6 text-center text-xs text-muted-foreground">
                  No workflow definitions yet.
                </p>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Editor */}
        <div className="min-w-0 flex-1">
          {!editor ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              Select a definition to edit, or create a new one.
            </div>
          ) : (
            <ScrollArea className="h-full p-6">
              <div className="mx-auto flex max-w-2xl flex-col gap-4">
                <h3 className="text-base font-semibold">
                  {editor.id ? "Edit workflow definition" : "New workflow definition"}
                </h3>

                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">Name</span>
                  <input
                    autoFocus
                    value={editor.name}
                    onChange={(e) => setEditor({ ...editor, name: e.target.value })}
                    placeholder="e.g. Research Report"
                    className={inputClass}
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Input (JSON Schema)
                  </span>
                  <textarea
                    value={editor.inputText}
                    onChange={(e) => setEditor({ ...editor, inputText: e.target.value })}
                    spellCheck={false}
                    rows={12}
                    className={`${inputClass} resize-y font-mono text-xs`}
                  />
                  {jsonError && (
                    <span className="text-xs text-status-blocked">Invalid JSON: {jsonError}</span>
                  )}
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">Definition (DSL)</span>
                  <textarea
                    value={editor.definition}
                    onChange={(e) => setEditor({ ...editor, definition: e.target.value })}
                    spellCheck={false}
                    rows={6}
                    placeholder="research(topic) -> draft(depth) -> review"
                    className={`${inputClass} resize-y font-mono text-xs`}
                  />
                </label>

                {saveError && <p className="text-sm text-status-blocked">{saveError}</p>}

                <div className="flex items-center gap-2">
                  <Button onClick={save} disabled={!editor.name.trim() || saving}>
                    {editor.id ? "Save changes" : "Create"}
                  </Button>
                  <Button variant="outline" onClick={() => setEditor(null)}>
                    Cancel
                  </Button>
                </div>
              </div>
            </ScrollArea>
          )}
        </div>
      </div>

      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)}>
        <div className="text-base font-semibold">Delete workflow definition</div>
        <p className="mt-2 text-sm text-muted-foreground">
          Delete{" "}
          <span className="font-medium text-foreground">{confirmDelete?.name}</span>? This
          can&apos;t be undone.
        </p>
        {deleteError && <p className="mt-3 text-sm text-status-blocked">{deleteError}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => setConfirmDelete(null)}>
            Cancel
          </Button>
          <Button size="sm" variant="destructive" disabled={deleteWd.isPending} onClick={doDelete}>
            Delete
          </Button>
        </div>
      </Dialog>
    </AppShell>
  );
}
