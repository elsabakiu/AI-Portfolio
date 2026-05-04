import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Pool } from "pg";
import { logger } from "./logger.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const migrationsDir = path.resolve(__dirname, "..", "..", "..", "infra", "migrations");

export function createDb(config) {
  const pool = new Pool({
    connectionString: config.databaseUrl,
    ssl: config.isProduction ? { rejectUnauthorized: false } : undefined,
  });

  async function query(text, params = []) {
    return pool.query(text, params);
  }

  async function withTransaction(callback) {
    const client = await pool.connect();
    try {
      await client.query("BEGIN");
      const result = await callback(client);
      await client.query("COMMIT");
      return result;
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async function migrate() {
    await query(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `);

    const files = (await fs.readdir(migrationsDir))
      .filter((file) => file.endsWith(".sql"))
      .sort();

    for (const file of files) {
      const { rowCount } = await query(
        "SELECT 1 FROM schema_migrations WHERE version = $1",
        [file]
      );
      if (rowCount > 0) continue;

      const sql = await fs.readFile(path.join(migrationsDir, file), "utf8");
      await withTransaction(async (client) => {
        await client.query(sql);
        await client.query(
          "INSERT INTO schema_migrations (version) VALUES ($1)",
          [file]
        );
      });

      logger.info("Applied database migration", { version: file });
    }
  }

  async function healthcheck() {
    await query("SELECT 1");
  }

  async function close() {
    await pool.end();
  }

  return {
    pool,
    query,
    withTransaction,
    migrate,
    healthcheck,
    close,
  };
}
