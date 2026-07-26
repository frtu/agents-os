import { Sheet, SheetHeader } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { ArtifactViewer } from "@/features/artifacts/ArtifactViewer";
import { useArtifact } from "@/hooks/queries";
import { useUiStore } from "@/store/ui";

export function ArtifactSheet() {
  const panel = useUiStore((s) => s.panel);
  const closePanel = useUiStore((s) => s.closePanel);
  const open = panel.kind === "artifact";
  const artifactId = panel.kind === "artifact" ? panel.artifactId : undefined;
  const { data: artifact, isLoading } = useArtifact(artifactId);

  return (
    <Sheet open={open} onClose={closePanel}>
      <SheetHeader
        title={artifact?.name ?? "Artifact"}
        description={artifact ? `${artifact.type} · v${artifact.version} · ${artifact.createdBy}` : undefined}
        onClose={closePanel}
      />
      <ScrollArea className="min-h-0 flex-1 p-4">
        {isLoading && <Skeleton className="h-40 w-full" />}
        {artifact && <ArtifactViewer artifact={artifact} />}
      </ScrollArea>
    </Sheet>
  );
}
