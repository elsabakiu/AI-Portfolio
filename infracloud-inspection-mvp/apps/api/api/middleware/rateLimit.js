import rateLimit from "express-rate-limit";

export function createRateLimitMiddleware(config) {
  return rateLimit({
    windowMs: config.rateLimitWindowMs,
    max: config.rateLimitMax,
    standardHeaders: true,
    legacyHeaders: false,
  });
}
