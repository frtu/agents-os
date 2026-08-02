import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { StoryDetailSheet } from "@/features/story/StoryDetailSheet";
import { TaskDetailSheet } from "@/features/story/TaskDetailSheet";
import { CreateStorySheet } from "@/features/story/CreateStorySheet";
import { EditStorySheet } from "@/features/story/EditStorySheet";
import { ArtifactSheet } from "@/features/artifacts/ArtifactSheet";
import { NotificationsSheet } from "@/features/notifications/NotificationsSheet";

export function AppShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={title} />
        <main className="min-h-0 flex-1 overflow-hidden">{children}</main>
      </div>

      {/* Global overlays driven by the UI store */}
      <StoryDetailSheet />
      <TaskDetailSheet />
      <CreateStorySheet />
      <EditStorySheet />
      <ArtifactSheet />
      <NotificationsSheet />
    </div>
  );
}
