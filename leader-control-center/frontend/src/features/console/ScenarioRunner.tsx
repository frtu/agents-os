import { useState } from "react";
import { CheckCircle2, ChevronDown, ChevronRight, Circle, Play, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ConsoleRequest, ConsoleResponse } from "@/features/console/client";
import { Exchange, StatusPill } from "@/features/console/parts";
import { runScenario, type Scenario, type StepResult } from "@/features/console/scenarios";

/** Runs one scenario and shows each step's outcome (spec 001 FR-7, FR-10). */
export function ScenarioRunner({
  scenario,
  onSent,
}: {
  scenario: Scenario;
  onSent: (request: ConsoleRequest, response: ConsoleResponse) => void;
}) {
  const [results, setResults] = useState<StepResult[]>([]);
  const [running, setRunning] = useState(false);
  const [open, setOpen] = useState<number | null>(null);

  async function run() {
    setRunning(true);
    setResults([]);
    setOpen(null);
    const final = await runScenario(scenario, (partial) => {
      setResults(partial);
      const latest = partial[partial.length - 1];
      if (latest.request && latest.response) onSent(latest.request, latest.response);
    });
    setRunning(false);
    const failed = final.findIndex((r) => !r.passed);
    if (failed >= 0) setOpen(failed);
  }

  const done = !running && results.length > 0;
  const passed = done && results.length === scenario.steps.length && results.every((r) => r.passed);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold">{scenario.title}</h2>
          <p className="mt-1 text-xs text-muted-foreground">{scenario.description}</p>
        </div>
        <Button size="sm" onClick={run} disabled={running}>
          <Play className="h-3.5 w-3.5" />
          {running ? "Running…" : results.length ? "Run again" : "Run"}
        </Button>
      </div>

      {done && (
        <p className={cn("text-sm font-medium", passed ? "text-status-completed" : "text-status-failed")}>
          {passed ? `Passed — ${results.length} steps` : `Failed at step ${results.length}: ${results[results.length - 1].name}`}
        </p>
      )}

      <ol className="flex flex-col divide-y divide-border rounded-md border border-border">
        {scenario.steps.map((step, i) => {
          const result = results[i];
          const Icon = !result ? Circle : result.passed ? CheckCircle2 : XCircle;
          const expanded = open === i && result;
          return (
            <li key={`${step.name}-${i}`} className="text-sm">
              <button
                type="button"
                disabled={!result}
                onClick={() => setOpen(expanded ? null : i)}
                className="flex w-full items-center gap-3 px-3 py-2 text-left disabled:cursor-default"
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    !result && (running && i === results.length ? "animate-pulse text-status-running" : "text-muted-foreground"),
                    result?.passed && "text-status-completed",
                    result && !result.passed && "text-status-failed",
                  )}
                />
                <span className="flex-1">{step.name}</span>
                {result?.response && <StatusPill response={result.response} />}
                {result && (expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />)}
              </button>
              {result && !result.passed && result.error && (
                <p className="px-10 pb-2 text-xs text-status-blocked">{result.error}</p>
              )}
              {expanded && result.request && (
                <div className="px-3 pb-3">
                  <Exchange request={result.request} response={result.response} />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
