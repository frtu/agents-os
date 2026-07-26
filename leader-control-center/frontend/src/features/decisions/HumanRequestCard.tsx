import { useState } from "react";
import type { DecisionKind, HumanRequest } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn, timeAgo } from "@/lib/utils";
import { useSubmitDecision } from "@/hooks/mutations";

const priorityStyle: Record<HumanRequest["priority"], string> = {
  high: "border-l-status-blocked",
  medium: "border-l-status-waiting",
  low: "border-l-status-todo",
};

export function HumanRequestCard({
  request,
  showContext = false,
}: {
  request: HumanRequest;
  showContext?: boolean;
}) {
  const submit = useSubmitDecision(request.executionId);
  const [comment, setComment] = useState("");

  const send = (decision: DecisionKind, selectedOption?: string) => {
    submit.mutate({ humanRequestId: request.id, input: { decision, selectedOption, comment: comment || undefined } });
  };

  const hasOptions = request.type === "ChooseOption" && request.options && request.options.length > 0;

  return (
    <div className={cn("rounded-md border border-l-4 border-border bg-card p-4", priorityStyle[request.priority])}>
      <div className="flex items-center justify-between gap-2">
        <Badge variant="outline">{request.type}</Badge>
        <span className="text-xs text-muted-foreground">{timeAgo(request.createdAt)}</span>
      </div>

      {showContext && (
        <div className="mt-2 text-xs text-muted-foreground">
          {request.initiativeTitle} · {request.storyTitle}
        </div>
      )}

      <p className="mt-2 text-sm">{request.prompt}</p>

      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Add a comment (optional)…"
        rows={2}
        className="mt-3 w-full resize-none rounded-md border border-input bg-background px-2 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />

      <div className="mt-3 flex flex-wrap gap-2">
        {hasOptions ? (
          request.options!.map((opt) => (
            <Button key={opt.id} size="sm" disabled={submit.isPending} onClick={() => send("SelectOption", opt.id)}>
              {opt.label}
            </Button>
          ))
        ) : (
          <>
            <Button size="sm" disabled={submit.isPending} onClick={() => send("Approve")}>
              Approve
            </Button>
            <Button size="sm" variant="secondary" disabled={submit.isPending} onClick={() => send("Continue")}>
              Continue
            </Button>
            <Button size="sm" variant="outline" disabled={submit.isPending} onClick={() => send("Reject")}>
              Reject
            </Button>
          </>
        )}
        <Button size="sm" variant="destructive" disabled={submit.isPending} onClick={() => send("Abort")}>
          Abort
        </Button>
      </div>
    </div>
  );
}
