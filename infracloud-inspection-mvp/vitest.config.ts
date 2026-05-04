import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  resolve: {
    alias: {
      "@web": path.resolve("apps/web/src"),
      "@ui": path.resolve("packages/ui/src"),
      "@schemas": path.resolve("packages/schemas/src"),
      "@config": path.resolve("packages/config/src"),
    },
  },
  test: {
    globals: true,
    environment: "node",
    setupFiles: ["./apps/web/test/setup.ts"],
    include: [
      "apps/web/src/**/*.test.ts",
      "apps/web/src/**/*.test.tsx",
      "apps/api/**/*.test.js",
    ],
    coverage: {
      reporter: ["text", "html"],
    },
  },
});
