import { cn } from "@/lib/utils";
import type { ConsoleRequest, ConsoleResponse } from "@/features/console/client";
import { buildUrl, failureDetail } from "@/features/console/client";

export const METHOD_STYLE: Record<string, string> = {
  GET: "text-status-ready",
  POST: "text-status-completed",
  PATCH: "text-status-running",
  PUT: "text-status-running",
  DELETE: "text-status-failed",
};

export function MethodTag({ method, className }: { method: string; className?: string }) {
  return <span className={cn("w-12 shrink-0 font-mono text-[11px] font-semibold", METHOD_STYLE[method], className)}>{method}</span>;
}

export function StatusPill({ response }: { response: ConsoleResponse }) {
  const tone = response.status === 0 || response.status >= 500
    ? "bg-status-failed/15 text-status-failed"
    : response.ok
      ? "bg-status-completed/15 text-status-completed"
      : "bg-status-waiting/20 text-status-running";
  return (
    <span className="inline-flex items-center gap-2 text-xs">
      <span className={cn("rounded-full px-2 py-0.5 font-mono font-semibold", tone)}>{response.status || "ERR"}</span>
      <span className="text-muted-foreground">{response.ms} ms</span>
    </span>
  );
}

export function JsonView({ value, className }: { value: unknown; className?: string }) {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return (
    <pre className={cn("max-h-[28rem] overflow-auto rounded-md bg-muted p-3 font-mono text-xs leading-relaxed", className)}>
      {text === undefined || text === "" || text === "null" ? <span className="text-muted-foreground">(empty body)</span> : text}
    </pre>
  );
}

/** Request line + body, then status + response — shared by history and scenario steps. */
export function Exchange({ request, response }: { request: ConsoleRequest; response?: ConsoleResponse }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 font-mono text-xs">
        <MethodTag method={request.method} />
        <span className="break-all">{buildUrl(request)}</span>
      </div>
      {request.body !== undefined && <JsonView value={request.body} className="max-h-48" />}
      {response && (
        <>
          <StatusPill response={response} />
          {!response.ok && <p className="text-sm text-status-blocked">{failureDetail(response)}</p>}
          <JsonView value={response.body} />
        </>
      )}
    </div>
  );
}
