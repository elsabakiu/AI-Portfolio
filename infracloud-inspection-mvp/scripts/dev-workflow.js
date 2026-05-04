import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";
import { loadEnvFile } from "./load-env.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

loadEnvFile(path.resolve(__dirname, "..", ".env"));

const child = spawn(
  "python3",
  ["-m", "uvicorn", "apps.workflow.app.main:app", "--port", "8001"],
  {
    cwd: path.resolve(__dirname, ".."),
    env: process.env,
    stdio: "inherit",
  },
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 0);
});

for (const event of ["SIGINT", "SIGTERM"]) {
  process.on(event, () => {
    child.kill(event);
  });
}
