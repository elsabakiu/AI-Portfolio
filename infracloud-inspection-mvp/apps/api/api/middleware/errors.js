import { AppError, toErrorResponse } from "../../lib/errors.js";
import { logger } from "../../lib/logger.js";
import { captureApiException } from "../../lib/sentry.js";

export function notFoundMiddleware(req, _res, next) {
  next(new AppError(404, "NOT_FOUND", `Route ${req.method} ${req.path} not found.`));
}

export function createErrorHandlerMiddleware(metrics) {
  return function errorHandlerMiddleware(error, req, res, _next) {
    const status = error instanceof AppError ? error.status : 500;
    const code = error instanceof AppError ? error.code : "INTERNAL_SERVER_ERROR";
    const message =
      error instanceof AppError
        ? error.message
        : "An unexpected server error occurred.";
    const details = error instanceof AppError ? error.details : undefined;

    if (status >= 400 && status < 500 && /^(INVALID_|MISSING_)/.test(code)) {
      metrics.increment("api_validation_failures", {
        route: req.path,
        method: req.method,
        code,
      });
    }

    if (status >= 500) {
      metrics.increment("api_server_errors", {
        route: req.path,
        method: req.method,
        code,
      });
    }

    captureApiException(error, req, {
      stage: details?.stage,
      suspicionId: details?.suspicion_id,
      workflowRunId: details?.workflow_run_id,
      details,
    });

    logger.error(message, {
      request_id: req.requestId,
      status_code: status,
      code,
      route: req.path,
      method: req.method,
      actor_id: req.actor?.userId,
      details,
      error,
    });

    res.status(status).json(
      toErrorResponse({
        code,
        message,
        requestId: req.requestId,
        details,
      })
    );
  };
}
