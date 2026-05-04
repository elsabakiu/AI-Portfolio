import path from "path";
import { fileURLToPath } from "url";
import { loadEnvFile } from "./load-env.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

loadEnvFile(path.resolve(__dirname, "..", ".env"));

await import("../apps/api/server.js");
