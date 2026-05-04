import express from "express";
import { createCorsMiddleware } from "./api/middleware/cors.js";
import { createErrorHandlerMiddleware, notFoundMiddleware } from "./api/middleware/errors.js";
import { requestIdMiddleware } from "./api/middleware/requestId.js";
import { createAuthMiddleware } from "./api/middleware/auth.js";
import { createRateLimitMiddleware } from "./api/middleware/rateLimit.js";
import { createRequestLoggerMiddleware } from "./api/middleware/requestLogger.js";
import { createHealthRouter } from "./api/routes/health.js";
import { createDraftsRouter } from "./api/routes/drafts.js";
import { createSubmissionsRouter } from "./api/routes/submissions.js";
import { createExtractionRouter } from "./api/routes/extraction.js";

export function createApp({ config, db, services }) {
  const app = express();

  app.disable("x-powered-by");
  app.use(express.json({ limit: config.jsonBodyLimit }));
  app.use(requestIdMiddleware);
  app.use(createAuthMiddleware(config));
  app.use(createRequestLoggerMiddleware(services.metrics));
  app.use(createCorsMiddleware(config));
  app.use(createRateLimitMiddleware(config));

  app.use("/api", createHealthRouter({ db, config, metrics: services.metrics }));
  app.use("/api", createDraftsRouter({ draftsService: services.drafts }));
  app.use("/api", createSubmissionsRouter({ submissionsService: services.submissions }));
  app.use(
    "/api",
    createExtractionRouter({
      extractionService: services.extraction,
      config,
    })
  );

  app.use(notFoundMiddleware);
  app.use(createErrorHandlerMiddleware(services.metrics));

  return app;
}
