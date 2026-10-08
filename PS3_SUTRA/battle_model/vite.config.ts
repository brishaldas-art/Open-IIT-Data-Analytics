import path from "path";
import { fileURLToPath } from "url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// The workbench is served by the SUTRA service itself: one origin, no CORS, no second host.
// `vite dev` proxies the API to a locally running service so the same code runs both ways.
const API = process.env.SUTRA_API || "http://127.0.0.1:8000";
const proxy = Object.fromEntries(
  ["/resolve", "/evidence", "/explain", "/health", "/v1", "/place", "/tasks", "/packs"].map((p) => [
    p,
    { target: API, changeOrigin: true },
  ]),
);

export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: { host: true, port: 5173, proxy },
  build: { outDir: "site", emptyOutDir: true, target: "es2020" },
});
