import { useEffect, useMemo, useState } from "react";
import Form from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import type { RJSFSchema, UiSchema } from "@rjsf/utils";
import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { errorText } from "@/lib/utils";
import { useInitiatives, useWorkflowDefinition, useWorkflowDefinitions } from "@/hooks/queries";
import { useCreateSchedule, usePreviewSchedule, useUpdateSchedule } from "@/hooks/mutations";
import type {
  OverlapPolicy,
  SchedulePreview,
  ScheduleSpec,
  ScheduleSpecKind,
  ScheduleView,
} from "@/types/domain";

// react-jsonschema-form renders its own submit button; we submit from the footer.
const RJSF_UI_SCHEMA: UiSchema = { "ui:submitButtonOptions": { norender: true } };

const inputClass =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary";

const OVERLAP_OPTIONS: { value: OverlapPolicy; label: string }[] = [
  { value: "Skip", label: "Skip if the previous run is still active" },
  { value: "BufferOne", label: "Queue one run until the previous one ends" },
  { value: "AllowParallel", label: "Start anyway (runs in parallel)" },
];

const CATCH_UP_OPTIONS = [
  { value: "PT15M", label: "15 minutes" },
  { value: "PT1H", label: "1 hour" },
  { value: "PT6H", label: "6 hours" },
  { value: "P1D", label: "1 day" },
];

type IntervalUnit = "M" | "H" | "D" | "W";
const UNIT_LABELS: Record<IntervalUnit, string> = { M: "minutes", H: "hours", D: "days", W: "weeks" };

const BROWSER_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone;

interface FormState {
  initiativeId: string;
  name: string;
  workflowDefinitionId: string;
  templateInput: Record<string, unknown>;
  kind: ScheduleSpecKind;
  at: string; // datetime-local value
  everyCount: number;
  everyUnit: IntervalUnit;
  expression: string;
  timezone: string;
  overlapPolicy: OverlapPolicy;
  catchUpWindow: string;
  keepCompleted: number;
  storyTitleTemplate: string;
  runNow: boolean;
}

function toDuration(count: number, unit: IntervalUnit): string {
  return unit === "D" || unit === "W" ? `P${count}${unit}` : `PT${count}${unit}`;
}

function fromDuration(iso?: string): { count: number; unit: IntervalUnit } {
  const m = /^P(?:(\d+)([WD]))?(?:T(\d+)([HM]))?$/.exec(iso ?? "");
  if (m?.[1]) return { count: Number(m[1]), unit: m[2] as IntervalUnit };
  if (m?.[3]) return { count: Number(m[3]), unit: m[4] as IntervalUnit };
  return { count: 1, unit: "D" };
}

function toLocalInput(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

function specFrom(f: FormState): ScheduleSpec {
  if (f.kind === "Once") return { kind: "Once", at: f.at ? new Date(f.at).toISOString() : undefined };
  if (f.kind === "Interval") return { kind: "Interval", every: toDuration(f.everyCount, f.everyUnit) };
  return { kind: "Cron", expression: f.expression.trim(), timezone: f.timezone.trim() };
}

function initialState(editing: ScheduleView | null, initiativeId: string): FormState {
  const s = editing?.schedule;
  const every = fromDuration(s?.spec.every);
  return {
    initiativeId: s?.initiativeId ?? initiativeId,
    name: s?.name ?? "",
    workflowDefinitionId: s?.workflowDefinitionId ?? "",
    templateInput: s?.templateInput ?? {},
    kind: s?.spec.kind ?? "Cron",
    at: toLocalInput(s?.spec.at),
    everyCount: every.count,
    everyUnit: every.unit,
    expression: s?.spec.expression ?? "0 9 * * MON",
    timezone: s?.spec.timezone ?? BROWSER_TZ,
    overlapPolicy: s?.overlapPolicy ?? "Skip",
    catchUpWindow: s?.catchUpWindow ?? "PT1H",
    keepCompleted: s?.keepCompleted ?? 5,
    storyTitleTemplate: s?.storyTitleTemplate ?? "{name} · {date}",
    runNow: false,
  };
}

export function formatOccurrence(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short", year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/** Create/edit drawer. Confirming the plain-language sentence is the approval
 * step (specs/planning/schedules.md §Creation Flow). */
export function ScheduleSheet({
  open,
  editing,
  onClose,
}: {
  open: boolean;
  editing: ScheduleView | null;
  onClose: () => void;
}) {
  const { data: summaries } = useInitiatives();
  const { data: definitions } = useWorkflowDefinitions();
  const initiatives = useMemo(
    () => (summaries ?? []).map((s) => s.initiative).filter((i) => i.status !== "Deleted"),
    [summaries],
  );

  const [form, setForm] = useState<FormState>(() => initialState(editing, ""));
  const [preview, setPreview] = useState<SchedulePreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const set = (changes: Partial<FormState>) => setForm((f) => ({ ...f, ...changes }));

  useEffect(() => {
    if (open) {
      setForm(initialState(editing, initiatives[0]?.id ?? ""));
      setPreview(null);
      setSaveError(null);
    }
    // Reset only when the drawer opens or switches schedule.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, editing?.schedule.id]);

  // Default the definition to the initiative's linked one, else the first.
  useEffect(() => {
    if (!open || form.workflowDefinitionId || !definitions?.length) return;
    const linked = initiatives.find((i) => i.id === form.initiativeId)?.workflowDefinitionId;
    set({ workflowDefinitionId: linked ?? definitions[0].id });
  }, [open, form.workflowDefinitionId, form.initiativeId, definitions, initiatives]);

  const { data: definition } = useWorkflowDefinition(form.workflowDefinitionId || undefined);

  // Live preview: the sentence + next occurrences the leader confirms.
  const previewSchedule = usePreviewSchedule();
  const spec = specFrom(form);
  const specKey = JSON.stringify([spec, form.overlapPolicy, form.storyTitleTemplate, form.name, form.initiativeId]);
  useEffect(() => {
    if (!open || !form.initiativeId) return;
    const timer = setTimeout(() => {
      previewSchedule.mutate(
        {
          initiativeId: form.initiativeId,
          name: form.name || "Untitled schedule",
          spec,
          overlapPolicy: form.overlapPolicy,
          storyTitleTemplate: form.storyTitleTemplate,
        },
        {
          onSuccess: (p) => {
            setPreview(p);
            setPreviewError(null);
          },
          onError: (e) => {
            setPreview(null);
            setPreviewError(errorText(e));
          },
        },
      );
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, specKey]);

  const create = useCreateSchedule();
  const update = useUpdateSchedule();
  const saving = create.isPending || update.isPending;
  const canSave =
    !!form.name.trim() && !!form.initiativeId && !!form.workflowDefinitionId && !!preview && !saving;

  const save = () => {
    setSaveError(null);
    const body = {
      name: form.name.trim(),
      workflowDefinitionId: form.workflowDefinitionId,
      templateInput: form.templateInput,
      spec,
      overlapPolicy: form.overlapPolicy,
      catchUpWindow: form.catchUpWindow,
      keepCompleted: form.keepCompleted,
      storyTitleTemplate: form.storyTitleTemplate,
    };
    const onError = (e: unknown) => setSaveError(errorText(e));
    if (editing) {
      update.mutate({ scheduleId: editing.schedule.id, input: body }, { onSuccess: onClose, onError });
    } else {
      create.mutate(
        { ...body, initiativeId: form.initiativeId, runNow: form.runNow },
        { onSuccess: onClose, onError },
      );
    }
  };

  return (
    <Sheet open={open} onClose={onClose}>
      <SheetHeader
        title={editing ? "Edit schedule" : "New schedule"}
        description="Create and start a Story from a workflow template at planned times."
        onClose={onClose}
      />

      <ScrollArea className="min-h-0 flex-1 p-4">
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Initiative</span>
            <select
              value={form.initiativeId}
              disabled={!!editing}
              onChange={(e) => set({ initiativeId: e.target.value, workflowDefinitionId: "" })}
              className={inputClass}
            >
              {initiatives.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.title}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Name</span>
            <input
              value={form.name}
              onChange={(e) => set({ name: e.target.value })}
              placeholder="e.g. Weekly risk review"
              className={inputClass}
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">Workflow template</span>
            <select
              value={form.workflowDefinitionId}
              onChange={(e) => set({ workflowDefinitionId: e.target.value, templateInput: {} })}
              className={inputClass}
            >
              {(definitions ?? []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>

          {definition && (
            <div className="rjsf-compact rounded-md border border-border p-3">
              <Form
                schema={definition.input as RJSFSchema}
                uiSchema={RJSF_UI_SCHEMA}
                validator={validator}
                formData={form.templateInput}
                onChange={(e) => set({ templateInput: e.formData ?? {} })}
              />
            </div>
          )}

          <div className="flex flex-col gap-2 rounded-md border border-border p-3">
            <span className="text-xs font-medium text-muted-foreground">When</span>
            <div className="flex gap-1">
              {(["Once", "Interval", "Cron"] as ScheduleSpecKind[]).map((k) => (
                <Button
                  key={k}
                  size="sm"
                  variant={form.kind === k ? "default" : "outline"}
                  onClick={() => set({ kind: k })}
                >
                  {k}
                </Button>
              ))}
            </div>
            {form.kind === "Once" && (
              <input
                type="datetime-local"
                value={form.at}
                onChange={(e) => set({ at: e.target.value })}
                className={inputClass}
              />
            )}
            {form.kind === "Interval" && (
              <div className="flex items-center gap-2 text-sm">
                <span>Every</span>
                <input
                  type="number"
                  min={1}
                  value={form.everyCount}
                  onChange={(e) => set({ everyCount: Math.max(1, Number(e.target.value)) })}
                  className={`${inputClass} w-24`}
                />
                <select
                  value={form.everyUnit}
                  onChange={(e) => set({ everyUnit: e.target.value as IntervalUnit })}
                  className={`${inputClass} w-32`}
                >
                  {(Object.keys(UNIT_LABELS) as IntervalUnit[]).map((u) => (
                    <option key={u} value={u}>
                      {UNIT_LABELS[u]}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {form.kind === "Cron" && (
              <div className="flex gap-2">
                <input
                  value={form.expression}
                  onChange={(e) => set({ expression: e.target.value })}
                  placeholder="0 9 * * MON"
                  spellCheck={false}
                  className={`${inputClass} font-mono`}
                />
                <input
                  value={form.timezone}
                  onChange={(e) => set({ timezone: e.target.value })}
                  placeholder="Europe/Paris"
                  className={`${inputClass} w-48`}
                />
              </div>
            )}
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">If the previous run is still active</span>
            <select
              value={form.overlapPolicy}
              onChange={(e) => set({ overlapPolicy: e.target.value as OverlapPolicy })}
              className={inputClass}
            >
              {OVERLAP_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground">Keep last N completed on board</span>
              <input
                type="number"
                min={0}
                value={form.keepCompleted}
                onChange={(e) => set({ keepCompleted: Math.max(0, Number(e.target.value)) })}
                className={inputClass}
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground">Catch up missed runs within</span>
              <select
                value={form.catchUpWindow}
                onChange={(e) => set({ catchUpWindow: e.target.value })}
                className={inputClass}
              >
                {CATCH_UP_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">
              Story title (<code>{"{name}"}</code> <code>{"{date}"}</code> <code>{"{datetime}"}</code>{" "}
              <code>{"{n}"}</code>)
            </span>
            <input
              value={form.storyTitleTemplate}
              onChange={(e) => set({ storyTitleTemplate: e.target.value })}
              className={inputClass}
            />
          </label>
        </div>
      </ScrollArea>

      <div className="flex flex-col gap-3 border-t border-border p-4">
        <div className="rounded-md bg-muted/50 p-3 text-sm">
          {preview ? (
            <>
              <p className="font-medium">{preview.sentence}</p>
              {preview.nextOccurrences.length > 0 && (
                <ul className="mt-2 list-disc pl-5 text-xs text-muted-foreground">
                  {preview.nextOccurrences.map((o) => (
                    <li key={o}>{formatOccurrence(o)}</li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <p className="text-muted-foreground">{previewError ?? "Fill in the schedule to see a preview."}</p>
          )}
        </div>
        {!editing && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.runNow}
              onChange={(e) => set({ runNow: e.target.checked })}
              className="h-4 w-4"
            />
            Run once now as a test
          </label>
        )}
        {saveError && <p className="text-sm text-status-blocked">{saveError}</p>}
        <Button onClick={save} disabled={!canSave}>
          {editing ? "Save changes" : "Confirm & create"}
        </Button>
      </div>
    </Sheet>
  );
}
