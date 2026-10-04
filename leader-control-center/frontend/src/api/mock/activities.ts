/**
 * In-memory Activity Definitions for mock mode (VITE_USE_MOCKS=true): CRUD and
 * a simplified render. Validation (bash -n, placeholder checks) and the webhook
 * test are backend-only (specs/execution/activity-definitions.md).
 */
import type {
  ActivityDefinition,
  ActivityDefinitionInput,
  RenderedActivity,
  WebhookTestResult,
} from "@/types/domain";
import { uid } from "@/lib/utils";

const definitions = new Map<string, ActivityDefinition>();
const PLACEHOLDER = /\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}/g;

function get(id: string): ActivityDefinition {
  const d = definitions.get(id);
  if (!d) throw new Error(`Activity definition not found: ${id}`);
  return d;
}

const shellQuote = (v: unknown) => `'${String(v ?? "").replace(/'/g, `'"'"'`)}'`;

export const mockActivities = {
  list: () => [...definitions.values()].sort((a, b) => a.name.localeCompare(b.name)),
  create(input: ActivityDefinitionInput): ActivityDefinition {
    if (!input.name?.trim() || !input.kind) throw new Error("Name and kind are required");
    const at = new Date().toISOString();
    const d: ActivityDefinition = {
      id: uid("act"), version: 1, createdAt: at, updatedAt: at, portfolioId: "portfolio_default",
      name: input.name, description: input.description ?? "", kind: input.kind,
      input: input.input ?? { type: "object", properties: {} },
      timeoutSeconds: input.timeoutSeconds ?? (input.kind === "Bash" ? 300 : 30),
      script: input.script, method: input.method ?? "POST", url: input.url,
      headers: input.headers ?? {}, contentType: input.contentType ?? "application/json",
      bodyTemplate: input.bodyTemplate,
    };
    definitions.set(d.id, d);
    return d;
  },
  update(id: string, input: ActivityDefinitionInput): ActivityDefinition {
    const d = get(id);
    const updated = { ...d, ...input, version: d.version + 1, updatedAt: new Date().toISOString() };
    definitions.set(id, updated);
    return updated;
  },
  remove(id: string) {
    get(id);
    definitions.delete(id);
  },
  render(id: string, values: Record<string, unknown>): RenderedActivity {
    const d = get(id);
    if (d.kind === "Bash") {
      return { kind: d.kind, headers: {}, script: (d.script ?? "").replace(PLACEHOLDER, (_, k) => shellQuote(values[k])) };
    }
    return {
      kind: d.kind, method: d.method, headers: d.headers,
      url: (d.url ?? "").replace(PLACEHOLDER, (_, k) => encodeURIComponent(String(values[k] ?? ""))),
      body: (d.bodyTemplate ?? "").replace(PLACEHOLDER, (_, k) => JSON.stringify(values[k] ?? null)),
    };
  },
  test(id: string, values: Record<string, unknown>): WebhookTestResult {
    return {
      request: this.render(id, values), durationMs: 0, responseHeaders: {},
      error: "Webhook tests are not sent in mock mode; run against the backend.",
    };
  },
};
