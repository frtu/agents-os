import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Archive, ChevronDown, ChevronRight, Pause, Pencil, Play, Plus, Zap } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { ExecutionStatusBadge } from "@/components/ui/status-badge";
import { cn, errorText } from "@/lib/utils";
import { useInitiatives, useScheduleRuns, useSchedules } from "@/hooks/queries";
import { useScheduleCommand, type ScheduleCommand } from "@/hooks/mutations";
import { useUiStore } from "@/store/ui";
import { ScheduleSheet, formatOccurrence } from "@/features/schedules/ScheduleSheet";
import type { ScheduleRun, ScheduleRunStatus, ScheduleStatus, ScheduleView } from "@/types/domain";

const STATUS_STYLE: Record<ScheduleStatus, string> = {
  Active: "bg-status-running/15 text-status-running",
  Paused: "bg-status-waiting/20 text-status-waiting",
  Completed: "bg-status-completed/15 text-status-completed",
  Archived: "bg-status-cancelled/15 text-status-cancelled",
};

const RUN_STYLE: Record<ScheduleRunStatus, string> = {
  Started: "bg-status-running/15 text-status-running",
  Buffered: "bg-status-ready/15 text-status-ready",
  Skipped: "bg-status-todo/15 text-status-todo",
  Missed: "bg-status-waiting/20 text-status-waiting",
  FailedToStart: "bg-status-failed/15 text-status-failed",
};

function RunBadge({ run }: { run: ScheduleRun }) {
  if (run.status === "Started" && run.outcome) return <ExecutionStatusBadge status={run.outcome} />;
  return <Badge className={RUN_STYLE[run.status]}>{run.status}</Badge>;
}

function RunHistory({ scheduleId }: { scheduleId: string }) {
  const { data: runs, isLoading } = useScheduleRuns(scheduleId);
  const openStory = useUiStore((s) => s.openStory);
  const navigate = useNavigate();
  if (isLoading) return <Skeleton className="h-16 w-full" />;
  if (!runs?.length) return <p className="py-3 text-xs text-muted-foreground">No runs yet.</p>;
  return (
    <table className="w-full text-xs">
      <thead className="text-left text-muted-foreground">
        <tr>
          <th className="py-1 font-medium">Occurrence</th>
          <th className="py-1 font-medium">Result</th>
          <th className="py-1 font-medium">Detail</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.id} className="border-t border-border">
            <td className="py-1.5">{formatOccurrence(run.scheduledFor)}</td>
            <td className="py-1.5">
              <RunBadge run={run} />
            </td>
            <td className="py-1.5 text-muted-foreground">
              {run.storyId ? (
                <button className="text-primary hover:underline" onClick={() => {
                    // The story drawer resolves its card from the board cache.
                    navigate("/");
                    openStory(run.storyId!);
                  }}>
                  Open story
                </button>
              ) : (
                run.error ?? run.reason ?? ""
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ScheduleRow({
  view,
  expanded,
  onToggle,
  onEdit,
  onCommand,
  busy,
}: {
  view: ScheduleView;
  expanded: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onCommand: (command: ScheduleCommand) => void;
  busy: boolean;
}) {
  const { schedule, sentence, nextOccurrences, lastRun } = view;
  const editable = schedule.status === "Active" || schedule.status === "Paused";
  return (
    <div className="rounded-md border border-border bg-card">
      <div className="flex items-start gap-3 p-3">
        <button onClick={onToggle} className="mt-0.5 text-muted-foreground" aria-label="Toggle run history">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium">{schedule.name}</span>
            <Badge className={STATUS_STYLE[schedule.status]}>{schedule.status}</Badge>
            {schedule.pauseReason && schedule.pauseReason !== "Manual" && (
              <Badge className="bg-status-blocked/15 text-status-blocked">
                {schedule.pauseReason === "ConsecutiveFailures" ? "Paused after failures" : "Template invalid"}
              </Badge>
            )}
            {lastRun && <RunBadge run={lastRun} />}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{sentence}</p>
          {nextOccurrences[0] && (
            <p className="mt-1 text-xs text-muted-foreground">Next: {formatOccurrence(nextOccurrences[0])}</p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {schedule.status === "Active" && (
            <Button size="sm" variant="outline" disabled={busy} onClick={() => onCommand("pause")}>
              <Pause className="h-3.5 w-3.5" />
              Pause
            </Button>
          )}
          {schedule.status === "Paused" && (
            <Button size="sm" variant="outline" disabled={busy} onClick={() => onCommand("resume")}>
              <Play className="h-3.5 w-3.5" />
              Resume
            </Button>
          )}
          {schedule.status !== "Archived" && (
            <Button size="sm" variant="outline" disabled={busy} onClick={() => onCommand("trigger")}>
              <Zap className="h-3.5 w-3.5" />
              Run now
            </Button>
          )}
          {editable && (
            <Button size="icon" variant="ghost" aria-label="Edit" onClick={onEdit}>
              <Pencil className="h-4 w-4" />
            </Button>
          )}
          {schedule.status !== "Archived" && (
            <Button size="icon" variant="ghost" aria-label="Archive" disabled={busy} onClick={() => onCommand("archive")}>
              <Archive className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      {expanded && (
        <div className="border-t border-border px-10 py-2">
          <RunHistory scheduleId={schedule.id} />
        </div>
      )}
    </div>
  );
}

export function SchedulesPage() {
  const { data: schedules, isLoading } = useSchedules();
  const { data: summaries } = useInitiatives();
  const command = useScheduleCommand();
  const [params] = useSearchParams();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [sheet, setSheet] = useState<{ open: boolean; editing: ScheduleView | null }>({
    open: false,
    editing: null,
  });
  const [confirmArchive, setConfirmArchive] = useState<ScheduleView | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Deep link from a board card's clock badge: /schedules?focus=<id>
  const focus = params.get("focus");
  useEffect(() => {
    if (focus) setExpanded((prev) => new Set(prev).add(focus));
  }, [focus]);

  const groups = useMemo(() => {
    const titles = new Map((summaries ?? []).map((s) => [s.initiative.id, s.initiative.title]));
    const byInitiative = new Map<string, ScheduleView[]>();
    for (const view of schedules ?? []) {
      const key = view.schedule.initiativeId;
      byInitiative.set(key, [...(byInitiative.get(key) ?? []), view]);
    }
    return [...byInitiative.entries()].map(([id, views]) => ({ id, title: titles.get(id) ?? id, views }));
  }, [schedules, summaries]);

  const run = (view: ScheduleView, cmd: ScheduleCommand) => {
    if (cmd === "archive") {
      setConfirmArchive(view);
      return;
    }
    setError(null);
    command.mutate(
      { scheduleId: view.schedule.id, command: cmd },
      { onError: (e) => setError(errorText(e)) },
    );
  };

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <AppShell title="Schedules">
      <ScrollArea className="h-full p-6">
        <div className="mx-auto flex max-w-4xl flex-col gap-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Recurring work: each occurrence creates and starts a new Story from a workflow template.
            </p>
            <Button size="sm" onClick={() => setSheet({ open: true, editing: null })}>
              <Plus className="h-3.5 w-3.5" />
              New schedule
            </Button>
          </div>

          {error && <p className="text-sm text-status-blocked">{error}</p>}

          {isLoading && Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}

          {schedules && schedules.length === 0 && (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No schedules yet. Create one to run a workflow template on a recurring basis.
            </p>
          )}

          {groups.map((group) => (
            <section key={group.id} className="flex flex-col gap-2">
              <h2 className="text-sm font-semibold text-muted-foreground">{group.title}</h2>
              {group.views.map((view) => (
                <div
                  key={view.schedule.id}
                  className={cn(focus === view.schedule.id && "rounded-md ring-2 ring-primary/40")}
                >
                  <ScheduleRow
                    view={view}
                    expanded={expanded.has(view.schedule.id)}
                    onToggle={() => toggle(view.schedule.id)}
                    onEdit={() => setSheet({ open: true, editing: view })}
                    onCommand={(cmd) => run(view, cmd)}
                    busy={command.isPending}
                  />
                </div>
              ))}
            </section>
          ))}
        </div>
      </ScrollArea>

      <ScheduleSheet
        open={sheet.open}
        editing={sheet.editing}
        onClose={() => setSheet({ open: false, editing: null })}
      />

      <Dialog open={!!confirmArchive} onClose={() => setConfirmArchive(null)}>
        <div className="text-base font-semibold">Archive schedule</div>
        <p className="mt-2 text-sm text-muted-foreground">
          Archive <span className="font-medium text-foreground">{confirmArchive?.schedule.name}</span>? No
          new Stories will be created. Existing Stories and run history are kept.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => setConfirmArchive(null)}>
            Cancel
          </Button>
          <Button
            size="sm"
            variant="destructive"
            disabled={command.isPending}
            onClick={() => {
              const target = confirmArchive;
              setConfirmArchive(null);
              if (target) {
                command.mutate(
                  { scheduleId: target.schedule.id, command: "archive" },
                  { onError: (e) => setError(errorText(e)) },
                );
              }
            }}
          >
            Archive
          </Button>
        </div>
      </Dialog>
    </AppShell>
  );
}
