import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 1500,
  },
  worker: {
    format: "es",
  },
});
