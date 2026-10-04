/**
 * One-click API Console scenarios (spec 001 FR-7..FR-11). Each scenario is a
 * fixed sequence of business commands/queries; inputs come from the live backend
 * state, never hard-coded ids. The backend side of each sequence is replayed in
 * backend/tests/test_api_console_scenarios.py — keep the two in step.
 */
import { failureDetail, send, type ConsoleRequest, type ConsoleResponse } from "@/features/console/client";
import { SchemaResolver } from "@/features/console/openapi";

type Ctx = Record<string, any>;

export interface Step {
  name: string;
  request: (ctx: Ctx) => ConsoleRequest;
  /** Return an error message when the response is wrong; otherwise capture values into ctx. */
  check?: (body: any, ctx: Ctx) => string | void;
}

export interface Scenario {
  id: string;
  title: string;
  description: string;
  steps: Step[];
}

export interface StepResult {
  name: string;
  request?: ConsoleRequest;
  response?: ConsoleResponse;
  passed: boolean;
  error?: string;
}

const resolver = new SchemaResolver();

const findInitiative: Step = {
  name: "Find an initiative",
  request: () => ({ method: "GET", path: "/initiatives" }),
  check: (body, ctx) => {
    if (!Array.isArray(body) || body.length === 0) return "No initiative exists — create one on the Board first";
    ctx.initiativeId = body[0].initiative.id;
    ctx.epicId = body[0].epicId;
  },
};

const SCHEDULE_SPEC = { kind: "Interval", every: "PT1H" };

const scheduleLifecycle: Scenario = {
  id: "schedule",
  title: "Schedule lifecycle",
  description: "Preview, create, trigger, read runs, pause, resume, archive (left Archived).",
  steps: [
    findInitiative,
    {
      name: "Find a workflow definition",
      request: () => ({ method: "GET", path: "/workflow-definitions" }),
      check: (body, ctx) => {
        if (!Array.isArray(body) || body.length === 0) return "No Workflow Definition exists — create one on the Workflow page first";
        ctx.workflowDefinitionId = body[0].id;
      },
    },
    {
      name: "Read its input schema",
      request: (ctx) => ({ method: "GET", path: `/workflow-definitions/${ctx.workflowDefinitionId}` }),
      check: (body, ctx) => {
        // spec 001 FR-9: templateInput is built from the definition's own schema.
        ctx.templateInput = resolver.example(body.input ?? {}, "Console test") ?? {};
      },
    },
    {
      name: "Preview",
      request: (ctx) => ({
        method: "POST",
        path: "/schedules/preview",
        body: { initiativeId: ctx.initiativeId, name: "Console test", spec: SCHEDULE_SPEC },
      }),
      check: (body) => (body.sentence ? undefined : "Preview returned no sentence"),
    },
    {
      name: "Create",
      request: (ctx) => ({
        method: "POST",
        path: "/schedules",
        body: {
          initiativeId: ctx.initiativeId,
          name: `Console test ${new Date().toLocaleTimeString()}`,
          workflowDefinitionId: ctx.workflowDefinitionId,
          templateInput: ctx.templateInput,
          spec: SCHEDULE_SPEC,
        },
      }),
      check: (body, ctx) => {
        ctx.scheduleId = body.schedule.id;
      },
    },
    {
      name: "Get",
      request: (ctx) => ({ method: "GET", path: `/schedules/${ctx.scheduleId}` }),
      check: (body) => expectStatus(body.schedule.status, "Active"),
    },
    {
      name: "Trigger (run now)",
      request: (ctx) => ({ method: "POST", path: `/schedules/${ctx.scheduleId}/trigger` }),
      check: (body) => (body.status === "FailedToStart" ? `Run failed to start: ${body.error ?? body.reason}` : undefined),
    },
    {
      name: "Read runs",
      request: (ctx) => ({ method: "GET", path: `/schedules/${ctx.scheduleId}/runs` }),
      check: (body) => (Array.isArray(body) && body.length > 0 ? undefined : "No run recorded"),
    },
    ...(["pause", "resume", "archive"] as const).map<Step>((command) => ({
      name: command[0].toUpperCase() + command.slice(1),
      request: (ctx) => ({ method: "POST", path: `/schedules/${ctx.scheduleId}/${command}` }),
      check: (body) =>
        expectStatus(body.schedule.status, { pause: "Paused", resume: "Active", archive: "Archived" }[command]),
    })),
  ],
};

const activityDefinition: Scenario = {
  id: "activity",
  title: "Activity Definition (Tasks)",
  description: "Create a temporary bash task, render it with parameters, read it, delete it.",
  steps: [
    {
      name: "Create bash definition",
      request: () => ({
        method: "POST",
        path: "/activity-definitions",
        body: {
          name: `Console test (bash) ${new Date().toLocaleTimeString()}`,
          description: "Temporary — created by the API Console",
          kind: "Bash",
          input: { type: "object", properties: { target: { type: "string", default: "world" } } },
          script: "echo hello {{target}}",
        },
      }),
      check: (body, ctx) => {
        ctx.activityId = body.id;
      },
    },
    {
      name: "Render with parameters",
      request: (ctx) => ({
        method: "POST",
        path: `/activity-definitions/${ctx.activityId}/render`,
        body: { input: { target: "console" } },
      }),
      check: (body) => (JSON.stringify(body).includes("console") ? undefined : "Parameter not rendered"),
    },
    {
      name: "Get",
      request: (ctx) => ({ method: "GET", path: `/activity-definitions/${ctx.activityId}` }),
    },
    {
      name: "Delete",
      request: (ctx) => ({ method: "DELETE", path: `/activity-definitions/${ctx.activityId}` }),
    },
  ],
};

const storyExecution: Scenario = {
  id: "story",
  title: "Story execution",
  description: "Create a Story, start it, read the execution, timeline and open decisions (Story is kept).",
  steps: [
    findInitiative,
    {
      name: "Create story",
      request: (ctx) => ({
        method: "POST",
        path: "/stories",
        body: { epicId: ctx.epicId, title: `Console test story ${new Date().toLocaleTimeString()}` },
      }),
      check: (body, ctx) => {
        ctx.storyId = body.id;
      },
    },
    {
      name: "Start",
      request: (ctx) => ({ method: "POST", path: `/stories/${ctx.storyId}/start` }),
      check: (body, ctx) => {
        ctx.executionId = body.id;
      },
    },
    { name: "Get execution", request: (ctx) => ({ method: "GET", path: `/executions/${ctx.executionId}` }) },
    { name: "Timeline", request: (ctx) => ({ method: "GET", path: `/executions/${ctx.executionId}/timeline` }) },
    { name: "Open decisions", request: (ctx) => ({ method: "GET", path: `/executions/${ctx.executionId}/decisions` }) },
  ],
};

const workflowDefinition: Scenario = {
  id: "workflow",
  title: "Workflow Definition",
  description: "Create, read, update and delete a temporary blueprint.",
  steps: [
    {
      name: "Create",
      request: () => ({
        method: "POST",
        path: "/workflow-definitions",
        body: { name: `Console test ${new Date().toLocaleTimeString()}`, input: { type: "object", properties: {} }, definition: "" },
      }),
      check: (body, ctx) => {
        ctx.wdId = body.id;
        ctx.wdName = body.name;
      },
    },
    { name: "Get", request: (ctx) => ({ method: "GET", path: `/workflow-definitions/${ctx.wdId}` }) },
    {
      name: "Update",
      request: (ctx) => ({ method: "PATCH", path: `/workflow-definitions/${ctx.wdId}`, body: { name: `${ctx.wdName} (edited)` } }),
      check: (body, ctx) => (body.name === `${ctx.wdName} (edited)` ? undefined : "Name not updated"),
    },
    { name: "Delete", request: (ctx) => ({ method: "DELETE", path: `/workflow-definitions/${ctx.wdId}` }) },
  ],
};

export const SCENARIOS: Scenario[] = [scheduleLifecycle, activityDefinition, storyExecution, workflowDefinition];

function expectStatus(actual: string, expected: string): string | void {
  if (actual !== expected) return `Expected status ${expected}, got ${actual}`;
}

/** Run steps in order; stop at the first failure and report why (spec 001 FR-10, P9). */
export async function runScenario(
  scenario: Scenario,
  onProgress: (results: StepResult[]) => void,
): Promise<StepResult[]> {
  const ctx: Ctx = {};
  const results: StepResult[] = [];
  for (const step of scenario.steps) {
    let request: ConsoleRequest | undefined;
    try {
      request = step.request(ctx);
      const response = await send(request);
      if (!response.ok) {
        results.push({ name: step.name, request, response, passed: false, error: `HTTP ${response.status || "—"}: ${failureDetail(response)}` });
      } else {
        const error = step.check?.(response.body, ctx) ?? undefined;
        results.push({ name: step.name, request, response, passed: !error, error });
      }
    } catch (e) {
      // A check that throws (unexpected response shape) is a failure with its reason, not a crash.
      results.push({ name: step.name, request, passed: false, error: e instanceof Error ? e.message : String(e) });
    }
    onProgress([...results]);
    if (!results[results.length - 1].passed) break;
  }
  return results;
}
