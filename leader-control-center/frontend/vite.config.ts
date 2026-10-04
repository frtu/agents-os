import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Ports are set by ../start.sh (from backend/.env); defaults otherwise.
    port: Number(process.env.FRONTEND_PORT ?? 5173),
    // Proxy real backend calls in dev when VITE_USE_MOCKS=false.
    proxy: {
      "/api": {
        target: `http://localhost:${process.env.BACKEND_PORT ?? 8010}`,
        changeOrigin: true,
        ws: true,
      },
      // Backend OpenAPI contract, read by the API Console (spec 001 FR-1).
      "/openapi.json": {
        target: `http://localhost:${process.env.BACKEND_PORT ?? 8010}`,
        changeOrigin: true,
      },
      // Local leader-assistant REST service (story-drafting chat).
      "/assistant": {
        target: "http://localhost:7860",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/assistant/, ""),
      },
    },
  },
});
