import { Router } from "express";
import { toSuccessResponse } from "../../lib/errors.js";

export function createHealthRouter({ db, config, metrics }) {
  const router = Router();

  router.get("/health", async (req, res, next) => {
    try {
      await db.healthcheck();
      res.json(
        toSuccessResponse(
          {
            environment: config.nodeEnv,
            upstreamConfigured: Boolean(config.langgraphServiceUrl),
            workflowProvider: "langgraph",
            database: "ok",
          },
          req.requestId
        )
      );
    } catch (error) {
      next(error);
    }
  });

  router.get("/ready", async (req, res, next) => {
    try {
      await db.healthcheck();
      metrics.setGauge("api_readiness", 1);
      res.json(
        toSuccessResponse(
          {
            ready: true,
            environment: config.nodeEnv,
            workflowProvider: "langgraph",
          },
          req.requestId
        )
      );
    } catch (error) {
      metrics.setGauge("api_readiness", 0);
      next(error);
    }
  });

  router.get("/metrics", (_req, res) => {
    res.setHeader("Content-Type", "text/plain; version=0.0.4");
    res.send(metrics.render());
  });

  return router;
}
