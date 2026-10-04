/**
 * Raw HTTP client for the API Console (spec 001 FR-3, FR-5). Unlike `api/http.ts`
 * it reaches any operation, always targets the real backend, and never throws on
 * an HTTP error: the console's job is to show what the backend answered.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const base = new URL(BASE_URL, window.location.origin);

/** Path prefix of the API (e.g. "/api/v1"); OpenAPI paths carry it, console paths do not. */
export const API_PREFIX = base.pathname.replace(/\/$/, "");
/** FastAPI publishes its contract at the server root. */
export const OPENAPI_URL = `${base.origin}/openapi.json`;

export interface ConsoleRequest {
  method: string;
  /** Path relative to the API prefix, e.g. "/schedules/sch_1/trigger". */
  path: string;
  query?: Record<string, string>;
  body?: unknown;
}

export interface ConsoleResponse {
  status: number; // 0 = the request never reached the backend
  ok: boolean;
  ms: number;
  body: unknown;
  /** Transport-level failure reason (network down, CORS…), when status is 0. */
  error?: string;
}

export function buildUrl(req: ConsoleRequest): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(req.query ?? {})) {
    if (value !== "") params.set(key, value);
  }
  const qs = params.toString();
  return `${base.origin}${API_PREFIX}${req.path}${qs ? `?${qs}` : ""}`;
}

export async function send(req: ConsoleRequest): Promise<ConsoleResponse> {
  const started = performance.now();
  try {
    const res = await fetch(buildUrl(req), {
      method: req.method,
      headers: req.body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: req.body !== undefined ? JSON.stringify(req.body) : undefined,
    });
    const text = await res.text();
    let body: unknown = text;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      /* keep raw text */
    }
    return { status: res.status, ok: res.ok, ms: Math.round(performance.now() - started), body };
  } catch (e) {
    // spec 001 FR-14 / P9: say why the backend was not reached, not just "failed".
    const reason = e instanceof Error ? e.message : String(e);
    return {
      status: 0,
      ok: false,
      ms: Math.round(performance.now() - started),
      body: null,
      error: `Backend not reachable at ${buildUrl(req)} (${reason})`,
    };
  }
}

/** The backend's own explanation of a failure: Problem+JSON `detail` or 422 validation errors. */
export function failureDetail(res: ConsoleResponse): string {
  if (res.error) return res.error;
  const body = res.body as { detail?: unknown; title?: string } | null;
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).join(".")}: ${d.msg ?? ""}`)
      .join("; ");
  }
  if (body?.title) return body.title;
  return typeof res.body === "string" && res.body ? res.body : `HTTP ${res.status}`;
}

/** Every `id` / `…Id` string in a response, for path-parameter suggestions (spec 001 FR-5). */
export function collectIds(body: unknown, found: Set<string> = new Set()): Set<string> {
  if (Array.isArray(body)) {
    body.forEach((item) => collectIds(item, found));
  } else if (body && typeof body === "object") {
    for (const [key, value] of Object.entries(body)) {
      if (typeof value === "string" && value && (key === "id" || key.endsWith("Id"))) found.add(value);
      else collectIds(value, found);
    }
  }
  return found;
}
