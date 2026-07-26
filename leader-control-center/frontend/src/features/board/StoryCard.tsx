import { AlertCircle, Play } from "lucide-react";
import type { StoryCardView } from "@/types/domain";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ColumnBadge } from "@/components/ui/status-badge";
import { useUiStore } from "@/store/ui";
import { useStartStory } from "@/hooks/mutations";

export function StoryCard({ card }: { card: StoryCardView }) {
  const openStory = useUiStore((s) => s.openStory);
  const startStory = useStartStory();
  const { story, column, execution, openHumanRequests } = card;
  const canStart = column === "Todo" || column === "Ready";

  return (
    <Card
      onClick={() => openStory(story.id, execution?.id)}
      className="cursor-pointer p-3 transition-colors hover:border-primary/50"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-medium leading-snug">{story.title}</span>
        <ColumnBadge column={column} />
      </div>
      {story.description && (
        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{story.description}</p>
      )}

      {execution && execution.status === "Running" && (
        <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-status-running transition-all"
            style={{ width: `${Math.round(execution.progress * 100)}%` }}
          />
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {openHumanRequests > 0 && (
            <span className="inline-flex items-center gap-1 text-status-blocked">
              <AlertCircle className="h-3.5 w-3.5" />
              {openHumanRequests} need{openHumanRequests === 1 ? "s" : ""} you
            </span>
          )}
        </div>
        {canStart && (
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              startStory.mutate(story.id);
            }}
            disabled={startStory.isPending}
          >
            <Play className="h-3.5 w-3.5" />
            Start
          </Button>
        )}
      </div>
    </Card>
  );
}
