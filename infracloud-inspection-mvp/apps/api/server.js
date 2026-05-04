import { createApp } from "./app.js";
import { loadConfig } from "./config/index.js";
import { createDb } from "./lib/db.js";
import { logger } from "./lib/logger.js";
import { createMetricsRegistry } from "./lib/metrics.js";
import { captureServerException, initSentry } from "./lib/sentry.js";
import { createAuditService } from "./services/audit.js";
import { createDraftsService } from "./services/drafts.js";
import { createExtractionService } from "./services/extraction.js";
import { createInspectionCasesService } from "./services/inspectionCases.js";
import { createSubmissionsService } from "./services/submissions.js";

const config = loadConfig();
initSentry(config);

const db = createDb(config);
const metrics = createMetricsRegistry({
  service: "infracloud-review-api",
  environment: config.nodeEnv,
});

const inspectionCases = createInspectionCasesService(db);
const audit = createAuditService(db);
const drafts = createDraftsService(db, inspectionCases, audit, metrics);
const submissions = createSubmissionsService(db, inspectionCases, audit, metrics);
const extraction = createExtractionService(db, config, inspectionCases, audit, metrics);

const app = createApp({
  config,
  db,
  services: {
    inspectionCases,
    audit,
    drafts,
    submissions,
    extraction,
    metrics,
  },
});

process.on("uncaughtException", (error) => {
  metrics.increment("api_process_exceptions", { kind: "uncaughtException" });
  captureServerException(error, { kind: "uncaughtException" });
  logger.error("Uncaught exception in API process", { error });
});

process.on("unhandledRejection", (reason) => {
  metrics.increment("api_process_exceptions", { kind: "unhandledRejection" });
  const error = reason instanceof Error ? reason : new Error(String(reason));
  captureServerException(error, { kind: "unhandledRejection" });
  logger.error("Unhandled rejection in API process", { error });
});

db.migrate()
  .then(() => db.healthcheck())
  .then(() => {
    metrics.setGauge("api_readiness", 1);
    app.listen(config.port, "127.0.0.1", () => {
      logger.info("InfraCloud review server listening", {
        environment: config.nodeEnv,
        port: config.port,
      });
    });
  })
  .catch((error) => {
    metrics.setGauge("api_readiness", 0);
    captureServerException(error, { stage: "startup" });
    logger.error("Failed to start API server", {
      error,
    });
    process.exit(1);
  });
