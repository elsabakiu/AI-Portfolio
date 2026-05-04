import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { sentryVitePlugin } from "@sentry/vite-plugin";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const plugins = [react()];

  if (env.SENTRY_AUTH_TOKEN && env.SENTRY_ORG && env.SENTRY_PROJECT) {
    plugins.push(
      sentryVitePlugin({
        authToken: env.SENTRY_AUTH_TOKEN,
        org: env.SENTRY_ORG,
        project: env.SENTRY_PROJECT,
        release: {
          name: env.VITE_SENTRY_RELEASE || env.SENTRY_RELEASE || "infracloud-inspection-mvp@dev",
        },
      })
    );
  }

  return {
    root: path.resolve("apps/web"),
    plugins,
    resolve: {
      alias: {
        "@web": path.resolve("apps/web/src"),
        "@ui": path.resolve("packages/ui/src"),
        "@schemas": path.resolve("packages/schemas/src"),
        "@config": path.resolve("packages/config/src"),
      },
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://localhost:8787",
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: path.resolve("dist"),
      emptyOutDir: true,
      sourcemap: true,
    },
  };
});
