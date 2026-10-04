/**
 * Minimal in-memory Schedules for mock mode (VITE_USE_MOCKS=true). Commands and
 * "Run now" behave like the backend; time-based firing, catch-up and overlap
 * rules live only in the real backend (specs/planning/schedules.md).
 */
import type {
  CreateScheduleInput,
  OverlapPolicy,
  Schedule,
  SchedulePreview,
  SchedulePreviewInput,
  ScheduleRun,
  ScheduleSpec,
  ScheduleView,
  UpdateScheduleInput,
} from "@/types/domain";
import { uid } from "@/lib/utils";
import { mockServer } from "@/api/mock/server";

const schedules = new Map<string, Schedule>();
const runs: ScheduleRun[] = [];

const OVERLAP_TEXT: Record<OverlapPolicy, string> = {
  Skip: "If the previous run is still active, skip this one.",
  BufferOne: "If the previous run is still active, queue one run for when it ends.",
  AllowParallel: "Start a new run even if the previous one is still active.",
};

function durationMs(iso: string): number {
  const m = /^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$/.exec(iso);
  if (!m) throw new Error(`Invalid ISO 8601 duration: ${iso}`);
  const [w, d, h, min, s] = m.slice(1).map((v) => Number(v ?? 0));
  return ((((w * 7 + d) * 24 + h) * 60 + min) * 60 + s) * 1000;
}

function nextOccurrences(spec: ScheduleSpec, n = 5): string[] {
  const now = Date.now();
  if (spec.kind === "Once") return spec.at && Date.parse(spec.at) > now ? [spec.at] : [];
  if (spec.kind === "Interval" && spec.every) {
    const every = durationMs(spec.every);
    const anchor = spec.anchor ? Date.parse(spec.anchor) : now;
    const k = now < anchor ? 0 : Math.floor((now - anchor) / every) + 1;
    return Array.from({ length: n }, (_, i) => new Date(anchor + every * (k + i)).toISOString());
  }
  return []; // cron evaluation is backend-only
}

function validate(spec: ScheduleSpec) {
  if (spec.kind === "Interval" && durationMs(spec.every ?? "") < 5 * 60_000) {
    throw new Error("Interval must be at least PT5M");
  }
  if (spec.kind === "Cron" && (!spec.expression || !spec.timezone)) {
    throw new Error("Cron schedules need an expression and an IANA timezone");
  }
  if (spec.kind === "Once" && !spec.at) throw new Error("Once schedules need `at`");
}

function describeSpec(spec: ScheduleSpec): string {
  if (spec.kind === "Once") return `Once at ${spec.at}`;
  if (spec.kind === "Interval") return `Every ${spec.every}`;
  return `On cron \`${spec.expression}\` (${spec.timezone})`;
}

function initiativeTitle(initiativeId: string): string {
  return (
    mockServer.getInitiatives().find((s) => s.initiative.id === initiativeId)?.initiative.title ??
    initiativeId
  );
}

function title(template: string, name: string, at: string): string {
  return template.replace("{name}", name).replace("{date}", at.slice(0, 10)).replace("{datetime}", at.slice(0, 16)).replace("{n}", "1");
}

function sentence(s: Pick<Schedule, "spec" | "overlapPolicy" | "storyTitleTemplate" | "name" | "initiativeId">) {
  const at = nextOccurrences(s.spec, 1)[0] ?? new Date().toISOString();
  return `${describeSpec(s.spec)}, create and start '${title(s.storyTitleTemplate, s.name, at)}' in ${initiativeTitle(s.initiativeId)}. ${OVERLAP_TEXT[s.overlapPolicy]}`;
}

function view(s: Schedule): ScheduleView {
  const mine = runs.filter((r) => r.scheduleId === s.id);
  return {
    schedule: s,
    sentence: sentence(s),
    nextOccurrences: s.status === "Active" ? nextOccurrences(s.spec) : [],
    lastRun: mine[0] ?? null,
  };
}

function get(scheduleId: string): Schedule {
  const s = schedules.get(scheduleId);
  if (!s) throw new Error(`Schedule not found: ${scheduleId}`);
  return s;
}

function save(s: Schedule, changes: Partial<Schedule>): Schedule {
  const updated = { ...s, ...changes, version: s.version + 1, updatedAt: new Date().toISOString() };
  schedules.set(s.id, updated);
  return updated;
}

export const mockSchedules = {
  list(initiativeId?: string): ScheduleView[] {
    return [...schedules.values()]
      .filter((s) => s.status !== "Archived" && (!initiativeId || s.initiativeId === initiativeId))
      .map(view);
  },
  get: (scheduleId: string) => view(get(scheduleId)),
  runs: (scheduleId: string) => runs.filter((r) => r.scheduleId === scheduleId),
  preview(input: SchedulePreviewInput): SchedulePreview {
    validate(input.spec);
    return {
      sentence: sentence({
        spec: input.spec, overlapPolicy: input.overlapPolicy ?? "Skip",
        storyTitleTemplate: input.storyTitleTemplate ?? "{name} · {date}",
        name: input.name, initiativeId: input.initiativeId,
      }),
      nextOccurrences: nextOccurrences(input.spec),
    };
  },
  create(input: CreateScheduleInput): ScheduleView {
    validate(input.spec);
    const at = new Date().toISOString();
    const s: Schedule = {
      id: uid("sched"), version: 1, createdAt: at, updatedAt: at,
      initiativeId: input.initiativeId, name: input.name,
      workflowDefinitionId: input.workflowDefinitionId, templateInput: input.templateInput,
      storyTitleTemplate: input.storyTitleTemplate ?? "{name} · {date}", spec: input.spec,
      overlapPolicy: input.overlapPolicy ?? "Skip", catchUpWindow: input.catchUpWindow ?? "PT1H",
      keepCompleted: input.keepCompleted ?? 5, status: "Active", consecutiveFailures: 0,
      nextOccurrenceAt: nextOccurrences(input.spec, 1)[0] ?? null, createdBy: "you@leader",
    };
    schedules.set(s.id, s);
    if (input.runNow) this.trigger(s.id);
    return view(get(s.id));
  },
  update(scheduleId: string, input: UpdateScheduleInput): ScheduleView {
    if (input.spec) validate(input.spec);
    return view(save(get(scheduleId), input as Partial<Schedule>));
  },
  pause: (scheduleId: string) => view(save(get(scheduleId), { status: "Paused", pauseReason: "Manual" })),
  resume: (scheduleId: string) =>
    view(save(get(scheduleId), { status: "Active", pauseReason: null, consecutiveFailures: 0 })),
  archive: (scheduleId: string) => view(save(get(scheduleId), { status: "Archived" })),
  trigger(scheduleId: string): ScheduleRun {
    const s = get(scheduleId);
    if (s.status === "Archived") throw new Error("Cannot run an archived schedule");
    const at = new Date().toISOString();
    const epicId = mockServer.getInitiatives().find((x) => x.initiative.id === s.initiativeId)?.epicId;
    if (!epicId) throw new Error(`Initiative not found: ${s.initiativeId}`);
    const story = mockServer.createStory({
      epicId, title: title(s.storyTitleTemplate, s.name, at),
      description: `Created by schedule '${s.name}' for the occurrence at ${at}.`,
      workflowDefinitionId: s.workflowDefinitionId, templateInput: s.templateInput,
    });
    Object.assign(story, { scheduleId: s.id, scheduledFor: at });
    mockServer.startStory(story.id);
    const run: ScheduleRun = {
      id: uid("srun"), scheduleId: s.id, scheduledFor: at, firedAt: at,
      status: "Started", storyId: story.id,
    };
    runs.unshift(run);
    return run;
  },
};
