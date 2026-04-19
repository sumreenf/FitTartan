import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/** Dev server proxies to FastAPI — backend must listen on this port (see npm run api / dev:all). */
const API = "http://127.0.0.1:8000";

const proxyPaths = [
  "/users",
  "/logs",
  "/agent",
  "/checkin",
  "/crowd",
  "/menu",
  "/meals",
  "/summary",
  "/health",
  "/motivation",
];

const proxy = Object.fromEntries(
  proxyPaths.map((p) => [p, { target: API, changeOrigin: true }])
);

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy,
  },
});
