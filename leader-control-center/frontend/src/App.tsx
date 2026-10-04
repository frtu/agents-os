import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { BoardPage } from "@/pages/BoardPage";
import { AttentionPage } from "@/pages/AttentionPage";
import { WorkflowPage } from "@/pages/WorkflowPage";
import { SchedulesPage } from "@/pages/SchedulesPage";
import { TasksPage } from "@/pages/TasksPage";

const router = createBrowserRouter([
  { path: "/", element: <BoardPage /> },
  { path: "/workflow", element: <WorkflowPage /> },
  { path: "/tasks", element: <TasksPage /> },
  { path: "/schedules", element: <SchedulesPage /> },
  { path: "/attention", element: <AttentionPage /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
