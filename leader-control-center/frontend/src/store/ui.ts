import { create } from "zustand";

type DetailPanel =
  | { kind: "none" }
  | { kind: "story"; storyId: string; executionId?: string }
  | { kind: "task"; taskId: string; storyId: string }
  | { kind: "artifact"; artifactId: string };

interface UiState {
  // Which initiative board is expanded on the board page.
  collapsedInitiatives: Record<string, boolean>;
  toggleInitiative: (id: string) => void;

  // Right-hand detail panel (story / task / artifact inspector).
  panel: DetailPanel;
  openStory: (storyId: string, executionId?: string) => void;
  openTask: (taskId: string, storyId: string) => void;
  openArtifact: (artifactId: string) => void;
  closePanel: () => void;

  // Notifications flyout.
  notificationsOpen: boolean;
  setNotificationsOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  collapsedInitiatives: {},
  toggleInitiative: (id) =>
    set((s) => ({ collapsedInitiatives: { ...s.collapsedInitiatives, [id]: !s.collapsedInitiatives[id] } })),

  panel: { kind: "none" },
  openStory: (storyId, executionId) => set({ panel: { kind: "story", storyId, executionId } }),
  openTask: (taskId, storyId) => set({ panel: { kind: "task", taskId, storyId } }),
  openArtifact: (artifactId) => set({ panel: { kind: "artifact", artifactId } }),
  closePanel: () => set({ panel: { kind: "none" } }),

  notificationsOpen: false,
  setNotificationsOpen: (open) => set({ notificationsOpen: open }),
}));
