import * as Sentry from "@sentry/node";
import { redactSensitiveData } from "./redact.js";

let sentryEnabled = false;

export function initSentry(config) {
  if (!config.sentryDsn) {
    return;
  }

  Sentry.init({
    dsn: config.sentryDsn,
    environment: config.sentryEnvironment,
    release: config.sentryRelease,
    tracesSampleRate: config.sentryTracesSampleRate,
    sendDefaultPii: false,
  });

  sentryEnabled = true;
}

export function isSentryEnabled() {
  return sentryEnabled;
}

export function captureApiException(error, req, extra = {}) {
  if (!sentryEnabled) return;

  Sentry.withScope((scope) => {
    scope.setTag("service", "api");
    scope.setTag("environment", process.env.NODE_ENV || "development");
    scope.setTag("route", req.path);
    scope.setTag("method", req.method);

    if (extra.stage) scope.setTag("workflow_stage", extra.stage);
    if (extra.suspicionId) scope.setTag("suspicion_id", String(extra.suspicionId));
    if (extra.workflowRunId) scope.setTag("workflow_run_id", String(extra.workflowRunId));

    if (req.requestId) scope.setTag("request_id", req.requestId);
    if (req.actor?.userId) {
      scope.setUser({
        id: req.actor.userId,
        role: req.actor.role,
      });
    }

    scope.setContext("request", {
      ...redactSensitiveData({
        request_id: req.requestId,
        path: req.path,
        method: req.method,
        actor_id: req.actor?.userId,
        actor_role: req.actor?.role,
        suspicion_id: extra.suspicionId ?? req.body?.suspicion_id ?? req.params?.suspicionId,
      }),
    });

    if (extra.details) {
      scope.setContext("details", redactSensitiveData(extra.details));
    }

    Sentry.captureException(error);
  });
}

export function captureServerException(error, context = {}) {
  if (!sentryEnabled) return;

  Sentry.withScope((scope) => {
    scope.setTag("service", "api");
    for (const [key, value] of Object.entries(context)) {
      if (value !== undefined && value !== null) {
        scope.setExtra(key, redactSensitiveData(value));
      }
    }
    Sentry.captureException(error);
  });
}

export function addBreadcrumb(crumb) {
  if (!sentryEnabled) return;
  Sentry.addBreadcrumb(crumb);
}
