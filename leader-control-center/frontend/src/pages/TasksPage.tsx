import { useEffect, useState } from "react";
import { Eye, Plus, Send, Terminal, Trash2, Webhook, X } from "lucide-react";
import { FormBuilder } from "@ginkgo-bioworks/react-json-schema-form-builder";
import Form from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import type { RJSFSchema, UiSchema } from "@rjsf/utils";
import "bootstrap/dist/css/bootstrap.min.css";
import type {
  ActivityDefinition,
  ActivityKind,
  RenderedActivity,
  WebhookMethod,
  WebhookTestResult,
} from "@/types/domain";
import { AppShell } from "@/components/layout/AppShell";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { cn, errorText } from "@/lib/utils";
import { useActivityDefinitions } from "@/hooks/queries";
import {
  useDeleteActivityDefinition,
  useRenderActivityDefinition,
  useSaveActivityDefinition,
  useTestActivityDefinition,
} from "@/hooks/mutations";

const inputClass =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary";
const monoClass = `${inputClass} resize-y font-mono text-xs`;
const RJSF_UI_SCHEMA: UiSchema = { "ui:submitButtonOptions": { norender: true } };

const EMPTY_SCHEMA = JSON.stringify({ type: "object", required: [], properties: {} }, null, 2);
const SAMPLE_SCRIPT = "#!/usr/bin/env bash\nset -euo pipefail\n\necho \"Hello {{name}}\"\n";
const SAMPLE_BODY = '{\n  "text": {{message}}\n}';

interface HeaderRow {
  name: string;
  value: string;
}

interface EditorState {
  id: string | null; // null = creating
  name: string;
  description: string;
  kind: ActivityKind;
  inputText: string; // JSON Schema (string) driven by the visual builder
  uiSchemaText: string; // builder-managed; not persisted
  timeoutSeconds: number;
  script: string;
  method: WebhookMethod;
  url: string;
  headers: HeaderRow[];
  contentType: string;
  bodyTemplate: string;
}

function emptyEditor(kind: ActivityKind): EditorState {
  return {
    id: null, name: "", description: "", kind,
    inputText: EMPTY_SCHEMA, uiSchemaText: "{}",
    timeoutSeconds: kind === "Bash" ? 300 : 30,
    script: SAMPLE_SCRIPT, method: "POST", url: "https://",
    headers: [], contentType: "application/json", bodyTemplate: SAMPLE_BODY,
  };
}

function editorFrom(d: ActivityDefinition): EditorState {
  return {
    id: d.id, name: d.name, description: d.description, kind: d.kind,
    inputText: JSON.stringify(d.input ?? {}, null, 2), uiSchemaText: "{}",
    timeoutSeconds: d.timeoutSeconds, script: d.script ?? "", method: d.method,
    url: d.url ?? "", headers: Object.entries(d.headers ?? {}).map(([name, value]) => ({ name, value })),
    contentType: d.contentType, bodyTemplate: d.bodyTemplate ?? "",
  };
}

function KindBadge({ kind }: { kind: ActivityKind }) {
  const Icon = kind === "Bash" ? Terminal : Webhook;
  return (
    <Badge variant="outline" className="shrink-0">
      <Icon className="h-3 w-3" />
      {kind}
    </Badge>
  );
}

/** "Try it": fill parameters from the saved definition's schema, then preview
 * (no side effects) or, for webhooks, send one test request. */
function TryIt({ definition }: { definition: ActivityDefinition }) {
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [rendered, setRendered] = useState<RenderedActivity | null>(null);
  const [result, setResult] = useState<WebhookTestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const render = useRenderActivityDefinition();
  const test = useTestActivityDefinition();

  useEffect(() => {
    setValues({});
    setRendered(null);
    setResult(null);
    setError(null);
  }, [definition.id, definition.version]);

  const run = (kind: "render" | "test") => {
    setError(null);
    setResult(null);
    const onError = (e: unknown) => setError(errorText(e));
    if (kind === "render") {
      render.mutate({ id: definition.id, input: values }, { onSuccess: setRendered, onError });
    } else {
      test.mutate(
        { id: definition.id, input: values },
        { onSuccess: (r) => { setResult(r); setRendered(r.request); }, onError },
      );
    }
  };

  return (
    <div className="flex flex-col gap-3 rounded-md border border-border p-3">
      <span className="text-sm font-semibold">Try it</span>
      <div className="rjsf-compact">
        <Form
          schema={definition.input as RJSFSchema}
          uiSchema={RJSF_UI_SCHEMA}
          validator={validator}
          formData={values}
          onChange={(e) => setValues(e.formData ?? {})}
        />
      </div>
      <div className="flex gap-2">
        <Button size="sm" variant="outline" disabled={render.isPending} onClick={() => run("render")}>
          <Eye className="h-3.5 w-3.5" />
          Preview
        </Button>
        {definition.kind === "Webhook" && (
          <Button size="sm" disabled={test.isPending} onClick={() => run("test")}>
            <Send className="h-3.5 w-3.5" />
            {test.isPending ? "Sending…" : "Send test"}
          </Button>
        )}
      </div>
      {definition.kind === "Bash" && (
        <p className="text-xs text-muted-foreground">
          Bash scripts are only syntax-checked here; they run on a Temporal worker.
        </p>
      )}
      {error && <p className="text-sm text-status-blocked">{error}</p>}
      {rendered && (
        <pre className="max-h-64 overflow-auto rounded-md bg-muted p-3 text-xs">
          {rendered.kind === "Bash"
            ? rendered.script
            : [
                `${rendered.method} ${rendered.url}`,
                ...Object.entries(rendered.headers).map(([k, v]) => `${k}: ${v}`),
                "",
                rendered.body ?? "",
              ].join("\n")}
        </pre>
      )}
      {result && (
        <div className="flex flex-col gap-1 text-xs">
          <span className={cn("font-medium", result.error || (result.status ?? 0) >= 400 ? "text-status-blocked" : "text-status-completed")}>
            {result.error ? result.error : `HTTP ${result.status}`} · {result.durationMs} ms
          </span>
          {result.responseBody && (
            <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3">{result.responseBody}</pre>
          )}
        </div>
      )}
    </div>
  );
}

export function TasksPage() {
  const { data: definitions, isLoading } = useActivityDefinitions();
  const save = useSaveActivityDefinition();
  const remove = useDeleteActivityDefinition();

  const [editor, setEditor] = useState<EditorState | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<ActivityDefinition | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const set = (changes: Partial<EditorState>) => setEditor((e) => (e ? { ...e, ...changes } : e));

  const saved = editor?.id ? definitions?.find((d) => d.id === editor.id) : undefined;

  const doSave = () => {
    if (!editor || !editor.name.trim()) return;
    setSaveError(null);
    let input: Record<string, unknown>;
    try {
      input = JSON.parse(editor.inputText || "{}");
    } catch (e) {
      setSaveError(`Parameters are not valid JSON: ${e instanceof Error ? e.message : e}`);
      return;
    }
    const common = {
      name: editor.name.trim(), description: editor.description, kind: editor.kind,
      input, timeoutSeconds: editor.timeoutSeconds,
    };
    const body =
      editor.kind === "Bash"
        ? { ...common, script: editor.script }
        : {
            ...common, method: editor.method, url: editor.url.trim(),
            headers: Object.fromEntries(
              editor.headers.filter((h) => h.name.trim()).map((h) => [h.name.trim(), h.value]),
            ),
            contentType: editor.contentType, bodyTemplate: editor.bodyTemplate,
          };
    save.mutate(
      { id: editor.id, input: body },
      {
        onSuccess: (d) => setEditor(editorFrom(d)),
        onError: (e) => setSaveError(errorText(e)),
      },
    );
  };

  const doDelete = () => {
    if (!confirmDelete) return;
    setDeleteError(null);
    remove.mutate(confirmDelete.id, {
      onSuccess: () => {
        if (editor?.id === confirmDelete.id) setEditor(null);
        setConfirmDelete(null);
      },
      onError: (e) => setDeleteError(errorText(e)),
    });
  };

  return (
    <AppShell title="Tasks">
      <div className="flex h-full">
        {/* List */}
        <div className="flex w-72 shrink-0 flex-col border-r border-border">
          <div className="flex items-center justify-between px-4 py-3">
            <h2 className="text-sm font-semibold text-muted-foreground">Activity definitions</h2>
          </div>
          <div className="flex gap-2 px-4 pb-3">
            <Button size="sm" variant="outline" onClick={() => { setSaveError(null); setEditor(emptyEditor("Bash")); }}>
              <Plus className="h-3.5 w-3.5" />
              Bash
            </Button>
            <Button size="sm" variant="outline" onClick={() => { setSaveError(null); setEditor(emptyEditor("Webhook")); }}>
              <Plus className="h-3.5 w-3.5" />
              Webhook
            </Button>
          </div>
          <ScrollArea className="min-h-0 flex-1 px-2 pb-2">
            <div className="flex flex-col gap-1">
              {isLoading && Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
              {definitions?.map((d) => (
                <button
                  key={d.id}
                  onClick={() => { setSaveError(null); setEditor(editorFrom(d)); }}
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors",
                    editor?.id === d.id
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                  )}
                >
                  <span className="min-w-0 flex-1 truncate font-medium">{d.name}</span>
                  <KindBadge kind={d.kind} />
                  <span
                    role="button"
                    tabIndex={0}
                    aria-label={`Delete ${d.name}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteError(null);
                      setConfirmDelete(d);
                    }}
                    className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </span>
                </button>
              ))}
              {definitions && definitions.length === 0 && (
                <p className="px-3 py-6 text-center text-xs text-muted-foreground">
                  No tasks yet. Create a bash script or a webhook.
                </p>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Editor */}
        <div className="min-w-0 flex-1">
          {!editor ? (
            <div className="flex h-full items-center justify-center px-6 text-center text-sm text-muted-foreground">
              Tasks are reusable building blocks for Temporal workflows: bash scripts or webhooks.
              Select one to edit, or create a new one.
            </div>
          ) : (
            <ScrollArea className="h-full p-6">
              <div className="mx-auto flex max-w-2xl flex-col gap-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-semibold">
                    {editor.id ? "Edit task" : "New task"}
                  </h3>
                  <KindBadge kind={editor.kind} />
                </div>

                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">Name</span>
                  <input
                    autoFocus
                    value={editor.name}
                    onChange={(e) => set({ name: e.target.value })}
                    placeholder={editor.kind === "Bash" ? "e.g. Disk usage report" : "e.g. Notify Slack"}
                    className={inputClass}
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">Description</span>
                  <input
                    value={editor.description}
                    onChange={(e) => set({ description: e.target.value })}
                    placeholder="What this task does"
                    className={inputClass}
                  />
                </label>

                <div className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Parameters (use them as <code>{"{{name}}"}</code> below)
                  </span>
                  <div className="rounded-md border border-border bg-background p-3">
                    <FormBuilder
                      schema={editor.inputText}
                      uischema={editor.uiSchemaText}
                      onChange={(schema: string, uischema: string) =>
                        set({ inputText: schema, uiSchemaText: uischema })
                      }
                    />
                  </div>
                </div>

                {editor.kind === "Bash" ? (
                  <label className="flex flex-col gap-1">
                    <span className="text-xs font-medium text-muted-foreground">
                      Script (values are shell-quoted when inserted)
                    </span>
                    <textarea
                      value={editor.script}
                      onChange={(e) => set({ script: e.target.value })}
                      spellCheck={false}
                      rows={12}
                      className={monoClass}
                    />
                  </label>
                ) : (
                  <>
                    <div className="flex gap-2">
                      <select
                        value={editor.method}
                        onChange={(e) => set({ method: e.target.value as WebhookMethod })}
                        className={`${inputClass} w-28`}
                      >
                        {(["POST", "PUT", "PATCH"] as WebhookMethod[]).map((m) => (
                          <option key={m}>{m}</option>
                        ))}
                      </select>
                      <input
                        value={editor.url}
                        onChange={(e) => set({ url: e.target.value })}
                        placeholder="https://hooks.example.com/notify"
                        spellCheck={false}
                        className={`${inputClass} font-mono`}
                      />
                    </div>

                    <div className="flex flex-col gap-2">
                      <span className="text-xs font-medium text-muted-foreground">
                        Headers (secrets as <code>{"${env:NAME}"}</code>, read from the backend environment)
                      </span>
                      {editor.headers.map((h, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <input
                            value={h.name}
                            onChange={(e) =>
                              set({ headers: editor.headers.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)) })
                            }
                            placeholder="Authorization"
                            className={`${inputClass} w-48`}
                          />
                          <input
                            value={h.value}
                            onChange={(e) =>
                              set({ headers: editor.headers.map((x, j) => (j === i ? { ...x, value: e.target.value } : x)) })
                            }
                            placeholder="Bearer ${env:HOOK_TOKEN}"
                            spellCheck={false}
                            className={`${inputClass} font-mono`}
                          />
                          <button
                            onClick={() => set({ headers: editor.headers.filter((_, j) => j !== i) })}
                            aria-label="Remove header"
                            className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                      <Button
                        size="sm"
                        variant="outline"
                        className="self-start"
                        onClick={() => set({ headers: [...editor.headers, { name: "", value: "" }] })}
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add header
                      </Button>
                    </div>

                    <label className="flex flex-col gap-1">
                      <span className="text-xs font-medium text-muted-foreground">Content type</span>
                      <input
                        value={editor.contentType}
                        onChange={(e) => set({ contentType: e.target.value })}
                        className={inputClass}
                      />
                    </label>

                    <label className="flex flex-col gap-1">
                      <span className="text-xs font-medium text-muted-foreground">
                        Payload template (JSON: write <code>{"{{name}}"}</code> as a whole value, it is
                        JSON-encoded)
                      </span>
                      <textarea
                        value={editor.bodyTemplate}
                        onChange={(e) => set({ bodyTemplate: e.target.value })}
                        spellCheck={false}
                        rows={8}
                        className={monoClass}
                      />
                    </label>
                  </>
                )}

                <label className="flex w-40 flex-col gap-1">
                  <span className="text-xs font-medium text-muted-foreground">Timeout (seconds)</span>
                  <input
                    type="number"
                    min={1}
                    value={editor.timeoutSeconds}
                    onChange={(e) => set({ timeoutSeconds: Math.max(1, Number(e.target.value)) })}
                    className={inputClass}
                  />
                </label>

                {saveError && <p className="text-sm text-status-blocked">{saveError}</p>}

                <div className="flex items-center gap-2">
                  <Button onClick={doSave} disabled={!editor.name.trim() || save.isPending}>
                    {editor.id ? "Save changes" : "Create"}
                  </Button>
                  <Button variant="outline" onClick={() => setEditor(null)}>
                    Cancel
                  </Button>
                </div>

                {saved ? (
                  <TryIt definition={saved} />
                ) : (
                  <p className="text-xs text-muted-foreground">Save the task to try it with parameters.</p>
                )}
              </div>
            </ScrollArea>
          )}
        </div>
      </div>

      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)}>
        <div className="text-base font-semibold">Delete task</div>
        <p className="mt-2 text-sm text-muted-foreground">
          Delete <span className="font-medium text-foreground">{confirmDelete?.name}</span>? This can&apos;t be
          undone.
        </p>
        {deleteError && <p className="mt-3 text-sm text-status-blocked">{deleteError}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => setConfirmDelete(null)}>
            Cancel
          </Button>
          <Button size="sm" variant="destructive" disabled={remove.isPending} onClick={doDelete}>
            Delete
          </Button>
        </div>
      </Dialog>
    </AppShell>
  );
}
