import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { BoardPage } from "@/pages/BoardPage";
import { AttentionPage } from "@/pages/AttentionPage";
import { WorkflowPage } from "@/pages/WorkflowPage";

const router = createBrowserRouter([
  { path: "/", element: <BoardPage /> },
  { path: "/workflow", element: <WorkflowPage /> },
  { path: "/attention", element: <AttentionPage /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
