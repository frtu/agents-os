import { useEffect, useMemo, useState } from "react";
import { FlaskConical, Search } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { USE_MOCKS } from "@/api";
import { collectIds, type ConsoleRequest, type ConsoleResponse } from "@/features/console/client";
import { loadContract, type LoadedContract } from "@/features/console/openapi";
import { Exchange, MethodTag, StatusPill } from "@/features/console/parts";
import { IDS_DATALIST, RequestBuilder } from "@/features/console/RequestBuilder";
import { ScenarioRunner } from "@/features/console/ScenarioRunner";
import { SCENARIOS } from "@/features/console/scenarios";
import { EventLog } from "@/features/console/EventLog";

interface HistoryEntry {
  n: number;
  at: string;
  request: ConsoleRequest;
  response: ConsoleResponse;
}

type Selection = { kind: "operation"; key: string } | { kind: "scenario"; id: string } | { kind: "history"; n: number };

/** Developer API Console — spec 001 (features/001-api-console). */
export function ConsolePage() {
  const [contract, setContract] = useState<LoadedContract | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [selection, setSelection] = useState<Selection>({ kind: "scenario", id: SCENARIOS[0].id });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [ids, setIds] = useState<string[]>([]);

  useEffect(() => {
    loadContract()
      .then(setContract)
      .catch((e: unknown) => setLoadError(e instanceof Error ? e.message : String(e)));
  }, []);

  function record(request: ConsoleRequest, response: ConsoleResponse) {
    // spec 001 FR-5 / FR-6: remember the exchange and any ids it revealed.
    setHistory((prev) => [{ n: (prev[0]?.n ?? 0) + 1, at: new Date().toLocaleTimeString(), request, response }, ...prev]);
    const found = [...collectIds(response.body)];
    if (found.length) setIds((prev) => [...new Set([...found, ...prev])].slice(0, 300));
  }

  const groups = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    const byTag = new Map<string, LoadedContract["operations"]>();
    for (const op of contract?.operations ?? []) {
      if (needle && !`${op.key} ${op.summary} ${op.tag}`.toLowerCase().includes(needle)) continue;
      byTag.set(op.tag, [...(byTag.get(op.tag) ?? []), op]);
    }
    return [...byTag.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [contract, filter]);

  const selectedOp = selection.kind === "operation" ? contract?.operations.find((o) => o.key === selection.key) : undefined;
  const selectedScenario = selection.kind === "scenario" ? SCENARIOS.find((s) => s.id === selection.id) : undefined;
  const selectedHistory = selection.kind === "history" ? history.find((h) => h.n === selection.n) : undefined;

  const itemClass = (active: boolean) =>
    cn(
      "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs transition-colors",
      active ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
    );

  return (
    <AppShell title="API Console">
      <datalist id={IDS_DATALIST}>
        {ids.map((id) => (
          <option key={id} value={id} />
        ))}
      </datalist>
      <div className="flex h-full">
        {/* Navigator: scenarios + endpoints */}
        <div className="flex w-72 shrink-0 flex-col border-r border-border">
          <div className="border-b border-border p-2">
            <div className="relative">
              <Search className="absolute left-2 top-2 h-4 w-4 text-muted-foreground" />
              <input
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter endpoints…"
                className="h-8 w-full rounded-md border border-input bg-background pl-8 pr-2 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
          </div>
          <ScrollArea className="flex-1 p-2">
            <p className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Scenarios</p>
            {SCENARIOS.map((s) => (
              <button
                key={s.id}
                type="button"
                className={itemClass(selection.kind === "scenario" && selection.id === s.id)}
                onClick={() => setSelection({ kind: "scenario", id: s.id })}
              >
                <FlaskConical className="h-3.5 w-3.5 shrink-0" />
                {s.title}
              </button>
            ))}

            <p className="px-2 pb-1 pt-4 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Endpoints</p>
            {!contract && !loadError && <Skeleton className="mx-2 h-24" />}
            {loadError && (
              // spec 001 FR-14: explain why the list is missing; scenarios stay usable.
              <p className="px-2 text-xs text-status-blocked">
                Endpoint list unavailable: {loadError}. Is the backend running? Scenarios will report the same reason.
              </p>
            )}
            {groups.map(([tag, ops]) => (
              <div key={tag} className="pb-2">
                <p className="px-2 py-1 text-[11px] font-medium text-foreground">{tag}</p>
                {ops.map((op) => (
                  <button
                    key={op.key}
                    type="button"
                    title={op.summary}
                    className={itemClass(selection.kind === "operation" && selection.key === op.key)}
                    onClick={() => setSelection({ kind: "operation", key: op.key })}
                  >
                    <MethodTag method={op.method} />
                    <span className="truncate font-mono">{op.path}</span>
                  </button>
                ))}
              </div>
            ))}
            {contract && groups.length === 0 && <p className="px-2 text-xs text-muted-foreground">No endpoint matches “{filter}”.</p>}
          </ScrollArea>
        </div>

        {/* Workbench */}
        <ScrollArea className="min-w-0 flex-1 p-6">
          {USE_MOCKS && (
            <p className="mb-4 rounded-md border border-status-waiting/40 bg-status-waiting/10 px-3 py-2 text-xs">
              The rest of the app is using the in-browser mock backend. The console always calls the real backend, so start it
              first (<code>uv run uvicorn app.main:app --port 8010</code>).
            </p>
          )}
          {selectedScenario && <ScenarioRunner key={selectedScenario.id} scenario={selectedScenario} onSent={record} />}
          {selectedOp && contract && <RequestBuilder key={selectedOp.key} op={selectedOp} resolver={contract.resolver} onSent={record} />}
          {selectedHistory && (
            <div className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold">
                Request #{selectedHistory.n} · {selectedHistory.at}
              </h2>
              <Exchange request={selectedHistory.request} response={selectedHistory.response} />
            </div>
          )}
        </ScrollArea>

        {/* History + realtime */}
        <div className="flex w-80 shrink-0 flex-col border-l border-border">
          <Tabs defaultValue="history" className="flex min-h-0 flex-1 flex-col p-3">
            <TabsList className="self-start">
              <TabsTrigger value="history">History ({history.length})</TabsTrigger>
              <TabsTrigger value="events">Events</TabsTrigger>
            </TabsList>
            <TabsContent value="history" className="min-h-0 flex-1">
              <ScrollArea className="h-full">
                {history.length === 0 && <p className="text-xs text-muted-foreground">Requests you send appear here.</p>}
                <ul className="flex flex-col gap-1">
                  {history.map((h) => (
                    <li key={h.n}>
                      <button
                        type="button"
                        onClick={() => setSelection({ kind: "history", n: h.n })}
                        className={cn(itemClass(selection.kind === "history" && selection.n === h.n), "flex-col items-stretch gap-1")}
                      >
                        <span className="flex items-center gap-2">
                          <MethodTag method={h.request.method} />
                          <span className="truncate font-mono">{h.request.path}</span>
                        </span>
                        <span className="flex items-center justify-between">
                          <StatusPill response={h.response} />
                          <span className="text-[11px]">{h.at}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </TabsContent>
            <TabsContent value="events" className="min-h-0 flex-1">
              <ScrollArea className="h-full">
                <EventLog />
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </AppShell>
  );
}
