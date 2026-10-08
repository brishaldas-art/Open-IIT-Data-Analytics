import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The frontend is served by the same Python service that owns the API (no second origin, no CORS).
export default defineConfig({
  plugins: [react()],
  base: './',                       // relative asset paths: works behind any host/proxy path
  build: { outDir: 'site', emptyOutDir: true, chunkSizeWarningLimit: 900 },
  server: { port: 5173, host: true },
})
