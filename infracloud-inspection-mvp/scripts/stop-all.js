import { spawnSync } from "child_process";

const patterns = [
  "node scripts/dev-api.js",
  "node scripts/dev-workflow.js",
  "node_modules/.bin/vite",
  "uvicorn apps.workflow.app.main:app",
  "apps/api/server.js",
];

const ports = [8787, 8001];

let killedAny = false;

function killPid(pid) {
  try {
    process.kill(Number(pid), "SIGTERM");
    killedAny = true;
  } catch {
    // Ignore already-stopped processes.
  }
}

for (const port of ports) {
  const result = spawnSync("lsof", ["-ti", `tcp:${port}`], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  });

  if (!result.stdout) {
    continue;
  }

  for (const pid of result.stdout.split(/\s+/).filter(Boolean)) {
    killPid(pid);
  }
}

for (const pattern of patterns) {
  const result = spawnSync("pkill", ["-f", pattern], {
    stdio: "ignore",
  });

  if (result.status === 0) {
    killedAny = true;
  }
}

if (killedAny) {
  console.log("Stopped InfraCloud local services.");
} else {
  console.log("No InfraCloud local services were running.");
}
