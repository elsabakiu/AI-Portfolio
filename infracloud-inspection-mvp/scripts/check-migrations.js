import fs from "node:fs/promises";
import path from "node:path";

const migrationsDir = path.resolve("infra/migrations");

async function main() {
  const files = (await fs.readdir(migrationsDir))
    .filter((file) => file.endsWith(".sql"))
    .sort();

  if (files.length === 0) {
    throw new Error("No SQL migrations found.");
  }

  let previousVersion = -1;

  for (const file of files) {
    const match = file.match(/^(\d+)_.*\.sql$/);
    if (!match) {
      throw new Error(`Migration "${file}" must start with a numeric prefix like 001_.`);
    }

    const version = Number(match[1]);
    if (version <= previousVersion) {
      throw new Error(`Migration "${file}" is out of order.`);
    }
    previousVersion = version;

    const sql = await fs.readFile(path.join(migrationsDir, file), "utf8");
    if (!sql.trim()) {
      throw new Error(`Migration "${file}" is empty.`);
    }

    if (!/(CREATE|ALTER|INSERT|UPDATE|DELETE|DROP)\s+/i.test(sql)) {
      throw new Error(`Migration "${file}" does not appear to contain SQL statements.`);
    }
  }

  console.log(`Validated ${files.length} migration files.`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
