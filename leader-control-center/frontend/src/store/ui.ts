import { create } from "zustand";

type DetailPanel =
  | { kind: "none" }
  | { kind: "story"; storyId: string; executionId?: string }
  | { kind: "task"; taskId: string; storyId: string }
  | { kind: "artifact"; artifactId: string }
  | { kind: "createStory"; initiativeId: string; epicId: string };

interface UiState {
  // Which initiative boards are expanded on the board page. Absent = collapsed,
  // so every board starts closed and its columns load only on unfold.
  expandedInitiatives: Record<string, boolean>;
  toggleInitiative: (id: string) => void;

  // Right-hand detail panel (story / task / artifact inspector).
  panel: DetailPanel;
  openStory: (storyId: string, executionId?: string) => void;
  openTask: (taskId: string, storyId: string) => void;
  openArtifact: (artifactId: string) => void;
  openCreateStory: (initiativeId: string, epicId: string) => void;
  closePanel: () => void;

  // Notifications flyout.
  notificationsOpen: boolean;
  setNotificationsOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  expandedInitiatives: {},
  toggleInitiative: (id) =>
    set((s) => ({ expandedInitiatives: { ...s.expandedInitiatives, [id]: !s.expandedInitiatives[id] } })),

  panel: { kind: "none" },
  openStory: (storyId, executionId) => set({ panel: { kind: "story", storyId, executionId } }),
  openTask: (taskId, storyId) => set({ panel: { kind: "task", taskId, storyId } }),
  openArtifact: (artifactId) => set({ panel: { kind: "artifact", artifactId } }),
  openCreateStory: (initiativeId, epicId) => set({ panel: { kind: "createStory", initiativeId, epicId } }),
  closePanel: () => set({ panel: { kind: "none" } }),

  notificationsOpen: false,
  setNotificationsOpen: (open) => set({ notificationsOpen: open }),
}));
