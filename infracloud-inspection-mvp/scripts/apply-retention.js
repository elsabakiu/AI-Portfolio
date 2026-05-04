import { Client } from "pg";

const databaseUrl = process.env.DATABASE_URL;
const retentionDays = Number(process.env.DATA_RETENTION_DAYS || "90");

if (!databaseUrl) {
  console.error("DATABASE_URL is required to run retention cleanup.");
  process.exit(1);
}

if (!Number.isInteger(retentionDays) || retentionDays <= 0) {
  console.error("DATA_RETENTION_DAYS must be a positive integer.");
  process.exit(1);
}

const client = new Client({ connectionString: databaseUrl });

async function main() {
  await client.connect();

  const retentionInterval = `${retentionDays} days`;
  const statements = [
    ["workflow_runs", "finished_at"],
    ["drafts", "saved_at"],
    ["submissions", "sent_at"],
    ["audit_events", "created_at"],
  ];

  const results = {};

  for (const [table, column] of statements) {
    const { rowCount } = await client.query(
      `DELETE FROM ${table} WHERE ${column} < NOW() - $1::interval`,
      [retentionInterval]
    );
    results[table] = rowCount;
  }

  console.log(JSON.stringify({ retentionDays, deleted: results }, null, 2));
}

main()
  .catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  })
  .finally(async () => {
    await client.end();
  });
