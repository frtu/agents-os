import type { Decision } from "@/types/domain";
import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/utils";

export function DecisionList({ decisions }: { decisions?: Decision[] }) {
  if (!decisions || decisions.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">No decisions recorded.</p>;
  }
  return (
    <div className="flex flex-col gap-2">
      {decisions.map((d) => (
        <div key={d.id} className="flex items-center justify-between gap-2 rounded-md border border-border p-2 text-sm">
          <div className="flex items-center gap-2">
            <Badge>{d.decision}</Badge>
            {d.comment && <span className="text-muted-foreground">{d.comment}</span>}
          </div>
          <span className="text-xs text-muted-foreground">
            {d.user} · {timeAgo(d.createdAt)}
          </span>
        </div>
      ))}
    </div>
  );
}
