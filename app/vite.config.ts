import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  // served at tools.justinwong.io/ep-farm-sim (worker/index.ts strips the prefix, so
  // the workers.dev root URL keeps working too — see wrangler.jsonc)
  base: "/ep-farm-sim/",
  plugins: [svelte()],
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 1500,
  },
  worker: {
    format: "es",
  },
});
