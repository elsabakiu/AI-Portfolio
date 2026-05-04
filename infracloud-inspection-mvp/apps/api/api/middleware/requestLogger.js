import { logger } from "../../lib/logger.js";

export function createRequestLoggerMiddleware(metrics) {
  return (req, res, next) => {
    const startedAt = performance.now();

    res.on("finish", () => {
      const durationMs = Number((performance.now() - startedAt).toFixed(2));
      const route = req.route?.path || req.path;

      metrics.increment("api_http_requests", {
        route,
        method: req.method,
        status_code: res.statusCode,
      });
      metrics.observe("api_http_request_duration_ms", durationMs, {
        route,
        method: req.method,
        status_code: res.statusCode,
      });

      logger.info("HTTP request completed", {
        request_id: req.requestId,
        route,
        method: req.method,
        status_code: res.statusCode,
        duration_ms: durationMs,
        actor_id: req.actor?.userId,
      });
    });

    next();
  };
}
