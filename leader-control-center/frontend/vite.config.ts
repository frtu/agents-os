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
    port: 5173,
    // Proxy real backend calls in dev when VITE_USE_MOCKS=false.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true,
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
