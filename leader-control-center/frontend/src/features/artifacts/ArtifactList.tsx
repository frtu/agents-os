import { FileText } from "lucide-react";
import type { Artifact } from "@/types/domain";
import { Badge } from "@/components/ui/badge";
import { timeAgo } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

export function ArtifactList({ artifacts }: { artifacts?: Artifact[] }) {
  const openArtifact = useUiStore((s) => s.openArtifact);

  if (!artifacts || artifacts.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No artifacts produced yet.</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      {artifacts.map((a) => (
        <button
          key={a.id}
          onClick={() => openArtifact(a.id)}
          className="flex items-center justify-between gap-3 rounded-md border border-border bg-card p-3 text-left hover:border-primary/50"
        >
          <div className="flex min-w-0 items-center gap-3">
            <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{a.name}</div>
              <div className="text-xs text-muted-foreground">
                {a.createdBy} · {timeAgo(a.createdAt)}
              </div>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Badge variant="secondary">{a.type}</Badge>
            <span className="text-xs text-muted-foreground">v{a.version}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
