import { Plus } from "lucide-react";
import { useUiStore } from "@/store/ui";

/** Empty add-story affordance at the bottom of a Todo column. */
export function AddStoryCard({ initiativeId, epicId }: { initiativeId: string; epicId: string }) {
  const openCreateStory = useUiStore((s) => s.openCreateStory);
  return (
    <button
      onClick={() => openCreateStory(initiativeId, epicId)}
      aria-label="Add story"
      className="flex items-center justify-center rounded-md border border-dashed border-border py-6 text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
    >
      <Plus className="h-5 w-5" />
    </button>
  );
}
