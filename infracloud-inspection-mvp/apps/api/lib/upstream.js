import { AppError } from "./errors.js";
import { logger } from "./logger.js";
import { addBreadcrumb } from "./sentry.js";

function shouldRetry(response) {
  return response.status >= 500 && response.status < 600;
}

export async function fetchWithRetry(url, options, config) {
  let lastError;

  for (let attempt = 0; attempt <= config.upstreamMaxRetries; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.upstreamTimeoutMs);

    try {
      addBreadcrumb({
        category: "upstream",
        message: "Dispatching upstream request",
        level: "info",
        data: {
          url,
          attempt,
        },
      });
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (shouldRetry(response) && attempt < config.upstreamMaxRetries) {
        logger.warn("Retrying upstream request", {
          stage: "upstream_retry",
          upstream_url: url,
          attempt,
          status_code: response.status,
        });
        continue;
      }

      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      lastError = error;
      if (attempt === config.upstreamMaxRetries) break;
      logger.warn("Upstream request attempt failed", {
        stage: "upstream_request",
        upstream_url: url,
        attempt,
        error: error instanceof Error ? error : new Error(String(error)),
      });
    }
  }

  throw new AppError(
    502,
    "UPSTREAM_UNAVAILABLE",
    "The extraction workflow is unavailable right now.",
    {
      reason: lastError instanceof Error ? lastError.message : String(lastError),
    }
  );
}
