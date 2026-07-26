import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { BoardPage } from "@/pages/BoardPage";
import { AttentionPage } from "@/pages/AttentionPage";

const router = createBrowserRouter([
  { path: "/", element: <BoardPage /> },
  { path: "/attention", element: <AttentionPage /> },
]);

export function App() {
  return <RouterProvider router={router} />;
}
