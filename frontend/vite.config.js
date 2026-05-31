import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendUrl = env.BACKEND_URL;

  if (!backendUrl) {
    throw new Error(
      "BACKEND_URL is not set. Create a .env file (see .env.example at repo root) and set BACKEND_URL."
    );
  }

  return {
    plugins: [react()],
    server: {
      proxy: {
        "/ingest": backendUrl,
        "/stream": backendUrl,
        "/health": backendUrl
      }
    }
  };
});

// Commit message suggestion:
//   "Add Vite dev proxy to backend via BACKEND_URL env var"
