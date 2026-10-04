import { useMemo, useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { send, type ConsoleRequest, type ConsoleResponse } from "@/features/console/client";
import { fillPath, type Operation, type SchemaResolver } from "@/features/console/openapi";
import { Exchange, MethodTag } from "@/features/console/parts";

export const IDS_DATALIST = "console-known-ids";

const inputClass =
  "h-8 w-full rounded-md border border-input bg-background px-2 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

/** Request builder for one operation (spec 001 FR-2..FR-4). Remount per operation via `key`. */
export function RequestBuilder({
  op,
  resolver,
  onSent,
}: {
  op: Operation;
  resolver: SchemaResolver;
  onSent: (request: ConsoleRequest, response: ConsoleResponse) => void;
}) {
  const initialBody = useMemo(
    () => (op.bodySchema ? JSON.stringify(resolver.example(op.bodySchema), null, 2) : ""),
    [op, resolver],
  );
  const [pathValues, setPathValues] = useState<Record<string, string>>({});
  const [queryValues, setQueryValues] = useState<Record<string, string>>({});
  const [bodyText, setBodyText] = useState(initialBody);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [last, setLast] = useState<{ request: ConsoleRequest; response: ConsoleResponse } | null>(null);

  const missing = op.pathParams.filter((p) => !pathValues[p.name]?.trim()).map((p) => p.name);

  async function submit() {
    let body: unknown;
    if (op.bodySchema && bodyText.trim()) {
      try {
        body = JSON.parse(bodyText);
      } catch (e) {
        // spec 001 FR-4: never send invalid JSON; say where it broke.
        setError(`Body is not valid JSON: ${e instanceof Error ? e.message : String(e)}`);
        return;
      }
    }
    setError(null);
    setSending(true);
    const request: ConsoleRequest = { method: op.method, path: fillPath(op.path, pathValues), query: queryValues, body };
    const response = await send(request);
    setSending(false);
    setLast({ request, response });
    onSent(request, response);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="flex items-center gap-2 font-mono text-sm">
          <MethodTag method={op.method} className="text-sm" />
          <span className="break-all">{op.path}</span>
        </div>
        {op.summary && <p className="mt-1 text-xs text-muted-foreground">{op.summary}</p>}
      </div>

      {[...op.pathParams.map((p) => ({ ...p, kind: "path" as const })), ...op.queryParams.map((p) => ({ ...p, kind: "query" as const }))]
        .map((p) => {
          const values = p.kind === "path" ? pathValues : queryValues;
          const set = p.kind === "path" ? setPathValues : setQueryValues;
          return (
            <label key={`${p.kind}:${p.name}`} className="flex flex-col gap-1 text-xs">
              <span className="text-muted-foreground">
                {p.kind === "path" ? `{${p.name}}` : `?${p.name}`}
                {p.required && <span className="text-status-blocked"> *</span>}
              </span>
              <input
                className={inputClass}
                value={values[p.name] ?? ""}
                list={p.kind === "path" ? IDS_DATALIST : undefined}
                placeholder={p.kind === "path" ? "pick or type an id" : "(optional)"}
                onChange={(e) => set((v) => ({ ...v, [p.name]: e.target.value }))}
              />
            </label>
          );
        })}

      {op.bodySchema && (
        <label className="flex flex-col gap-1 text-xs">
          <span className="flex items-center justify-between text-muted-foreground">
            JSON body
            <button type="button" className="hover:text-foreground" onClick={() => setBodyText(initialBody)}>
              reset example
            </button>
          </span>
          <textarea
            className="min-h-48 rounded-md border border-input bg-background p-2 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            spellCheck={false}
            value={bodyText}
            onChange={(e) => setBodyText(e.target.value)}
          />
        </label>
      )}

      <div className="flex items-center gap-3">
        <Button size="sm" onClick={submit} disabled={sending || missing.length > 0}>
          <Send className="h-3.5 w-3.5" />
          {sending ? "Sending…" : "Send"}
        </Button>
        {missing.length > 0 && <span className="text-xs text-muted-foreground">Fill {missing.map((m) => `{${m}}`).join(", ")}</span>}
      </div>
      {error && <p className="text-sm text-status-blocked">{error}</p>}

      {last && (
        <div className="border-t border-border pt-4">
          <Exchange request={last.request} response={last.response} />
        </div>
      )}
    </div>
  );
}
