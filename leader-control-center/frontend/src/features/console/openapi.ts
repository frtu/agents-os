/**
 * Loads the backend's OpenAPI document and turns it into console operations
 * (spec 001 FR-1, FR-2). The list follows the backend contract automatically,
 * so there is no per-endpoint UI to keep in step.
 */
import { API_PREFIX, OPENAPI_URL } from "@/features/console/client";

export type JsonSchema = Record<string, any>;

export interface Parameter {
  name: string;
  required: boolean;
  schema: JsonSchema;
}

export interface Operation {
  key: string; // "POST /schedules/{schedule_id}/trigger"
  method: string;
  path: string; // relative to API_PREFIX
  tag: string;
  summary: string;
  pathParams: Parameter[];
  queryParams: Parameter[];
  bodySchema?: JsonSchema;
}

interface OpenApiDoc {
  paths: Record<string, Record<string, any>>;
  components?: { schemas?: Record<string, JsonSchema> };
}

const METHODS = ["get", "post", "put", "patch", "delete"];

/**
 * Hand-picked examples for schemas whose generated placeholder would be rejected
 * (e.g. a ScheduleSpec needs `every` for Interval). Keyed by component name.
 */
const SCHEMA_EXAMPLES: Record<string, unknown> = {
  ScheduleSpec: { kind: "Interval", every: "PT1H" },
};

export class SchemaResolver {
  constructor(private components: Record<string, JsonSchema> = {}) {}

  /** Follow `$ref` and collapse nullable `anyOf` to its non-null branch. */
  resolve(schema: JsonSchema | undefined): JsonSchema {
    let current = schema ?? {};
    for (let i = 0; i < 10; i++) {
      if (current.$ref) {
        current = { ...this.components[refName(current.$ref)], __name: refName(current.$ref) };
      } else if (current.anyOf || current.oneOf) {
        const branches: JsonSchema[] = current.anyOf ?? current.oneOf;
        const branch = branches.find((b) => b.type !== "null") ?? branches[0];
        current = { ...branch, default: current.default ?? branch?.default };
      } else if (current.allOf?.length === 1) {
        current = current.allOf[0];
      } else {
        return current;
      }
    }
    return current;
  }

  /**
   * Example value for a schema: curated example → default → first enum → a
   * placeholder per type. Objects get their required properties plus those with
   * defaults. `text` is the placeholder for free strings.
   */
  example(schema: JsonSchema | undefined, text = "", depth = 0): unknown {
    const s = this.resolve(schema);
    if (s.__name && s.__name in SCHEMA_EXAMPLES) return structuredClone(SCHEMA_EXAMPLES[s.__name]);
    if (s.default !== undefined) return structuredClone(s.default);
    if (Array.isArray(s.enum) && s.enum.length) return s.enum[0];
    if (s.const !== undefined) return s.const;
    const type = Array.isArray(s.type) ? s.type.find((t: string) => t !== "null") : s.type;
    if (type === "object" || s.properties) {
      if (depth > 4) return {};
      const required = new Set<string>(s.required ?? []);
      const out: Record<string, unknown> = {};
      for (const [name, prop] of Object.entries<JsonSchema>(s.properties ?? {})) {
        const resolved = this.resolve(prop);
        if (required.has(name) || resolved.default !== undefined) {
          out[name] = this.example(prop, text, depth + 1);
        }
      }
      return out;
    }
    if (type === "array") return [];
    if (type === "integer" || type === "number") return s.minimum ?? 0;
    if (type === "boolean") return false;
    if (s.format === "date-time") return new Date(Date.now() + 3_600_000).toISOString();
    return text;
  }
}

function refName(ref: string): string {
  return ref.split("/").pop() ?? ref;
}

export interface LoadedContract {
  operations: Operation[];
  resolver: SchemaResolver;
}

export async function loadContract(): Promise<LoadedContract> {
  let res: Response;
  try {
    res = await fetch(OPENAPI_URL);
  } catch (e) {
    // spec 001 FR-14: name the URL and the reason.
    throw new Error(`Could not reach ${OPENAPI_URL} (${e instanceof Error ? e.message : String(e)})`);
  }
  if (!res.ok) throw new Error(`${OPENAPI_URL} answered HTTP ${res.status}`);
  const doc = (await res.json()) as OpenApiDoc;
  const resolver = new SchemaResolver(doc.components?.schemas);

  const operations: Operation[] = [];
  for (const [fullPath, item] of Object.entries(doc.paths)) {
    if (!fullPath.startsWith(API_PREFIX)) continue;
    const path = fullPath.slice(API_PREFIX.length) || "/";
    for (const method of METHODS) {
      const op = item[method];
      if (!op) continue;
      const params: any[] = [...(item.parameters ?? []), ...(op.parameters ?? [])];
      const toParam = (p: any): Parameter => ({ name: p.name, required: !!p.required, schema: p.schema ?? {} });
      operations.push({
        key: `${method.toUpperCase()} ${path}`,
        method: method.toUpperCase(),
        path,
        tag: op.tags?.[0] ?? "other",
        summary: op.summary ?? "",
        pathParams: params.filter((p) => p.in === "path").map(toParam),
        queryParams: params.filter((p) => p.in === "query").map(toParam),
        bodySchema: op.requestBody?.content?.["application/json"]?.schema,
      });
    }
  }
  return { operations, resolver };
}

/** Substitute `{name}` path parameters (URL-encoded). */
export function fillPath(path: string, values: Record<string, string>): string {
  return path.replace(/\{([^}]+)\}/g, (_, name: string) => encodeURIComponent(values[name] ?? ""));
}
