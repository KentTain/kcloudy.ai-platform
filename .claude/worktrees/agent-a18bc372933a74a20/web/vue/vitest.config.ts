import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [tailwindcss(), vue()],
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.ts", "tests/**/*.spec.ts"],
    exclude: ["**/e2e/**", "node_modules/**"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    extensions: [".js", ".ts", ".vue"],
  },
});
