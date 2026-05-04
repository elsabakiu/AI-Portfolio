const VALID_ENVIRONMENTS = new Set(["development", "staging", "production"]);
const VALID_AUTH_MODES = new Set(["disabled", "headers", "bearer"]);
const VALID_ROLES = new Set(["reviewer", "approver", "admin"]);

function parsePositiveInteger(value, fallback) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function parseOptionalList(value) {
  if (!value) return [];
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseOptionalJson(value, fallback) {
  if (!value) return fallback;
  try {
    return JSON.parse(value);
  } catch (error) {
    throw new Error(
      `Invalid JSON config value: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

export function loadConfig(env = process.env) {
  const nodeEnv = env.NODE_ENV || "development";
  if (!VALID_ENVIRONMENTS.has(nodeEnv)) {
    throw new Error(
      `Invalid NODE_ENV "${nodeEnv}". Use development, staging, or production.`
    );
  }

  const authMode = env.AUTH_MODE || (nodeEnv === "development" ? "headers" : "bearer");
  if (!VALID_AUTH_MODES.has(authMode)) {
    throw new Error(`Invalid AUTH_MODE "${authMode}". Use disabled, headers, or bearer.`);
  }
  if (nodeEnv !== "development" && authMode === "disabled") {
    throw new Error("AUTH_MODE=disabled is not allowed outside development.");
  }

  const port = parsePositiveInteger(env.PORT, 8787);
  const upstreamTimeoutMs = parsePositiveInteger(env.UPSTREAM_TIMEOUT_MS, 20000);
  const upstreamMaxRetries = parsePositiveInteger(env.UPSTREAM_MAX_RETRIES, 2);
  const langgraphServiceUrl = env.LANGGRAPH_SERVICE_URL || "http://127.0.0.1:8001";
  const databaseUrl =
    env.DATABASE_URL ||
    "postgresql://localhost:5432/infracloud_inspection_mvp";
  const corsOrigins = parseOptionalList(env.CORS_ALLOWED_ORIGINS);
  const rateLimitWindowMs = parsePositiveInteger(env.RATE_LIMIT_WINDOW_MS, 15 * 60 * 1000);
  const rateLimitMax = parsePositiveInteger(env.RATE_LIMIT_MAX_REQUESTS, 200);
  const jsonBodyLimit = env.JSON_BODY_LIMIT || "2mb";
  const uploadFileSizeLimitBytes = parsePositiveInteger(
    env.UPLOAD_FILE_SIZE_LIMIT_BYTES,
    15 * 1024 * 1024
  );
  const sentryDsn = env.SENTRY_DSN || "";
  const sentryEnvironment = env.SENTRY_ENVIRONMENT || nodeEnv;
  const sentryRelease = env.SENTRY_RELEASE || "infracloud-inspection-mvp@dev";
  const sentryTracesSampleRate = Number(env.SENTRY_TRACES_SAMPLE_RATE || "0.2");
  const authTokens = parseOptionalJson(env.AUTH_TOKENS_JSON, []).map((item) => {
    if (!item?.token || !item?.userId || !item?.role) {
      throw new Error("Each AUTH_TOKENS_JSON entry must include token, userId, and role.");
    }
    if (!VALID_ROLES.has(item.role)) {
      throw new Error(`Invalid auth role "${item.role}".`);
    }
    return {
      token: String(item.token),
      userId: String(item.userId),
      role: String(item.role),
      displayName: item.displayName ? String(item.displayName) : null,
    };
  });
  const dataRetentionDays = parsePositiveInteger(env.DATA_RETENTION_DAYS, 90);

  return {
    nodeEnv,
    isDevelopment: nodeEnv === "development",
    isStaging: nodeEnv === "staging",
    isProduction: nodeEnv === "production",
    port,
    langgraphServiceUrl,
    upstreamTimeoutMs,
    upstreamMaxRetries,
    databaseUrl,
    corsOrigins,
    rateLimitWindowMs,
    rateLimitMax,
    jsonBodyLimit,
    uploadFileSizeLimitBytes,
    sentryDsn,
    sentryEnvironment,
    sentryRelease,
    sentryTracesSampleRate,
    authMode,
    authTokens,
    dataRetentionDays,
  };
}
