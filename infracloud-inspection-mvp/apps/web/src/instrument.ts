import * as Sentry from "@sentry/react";

function getSessionId() {
  const storageKey = "infracloud-review-session-id";
  const existing = window.sessionStorage.getItem(storageKey);
  if (existing) return existing;

  const next = crypto.randomUUID();
  window.sessionStorage.setItem(storageKey, next);
  return next;
}

const dsn = import.meta.env.VITE_SENTRY_DSN;

if (dsn) {
  const sessionId = getSessionId();

  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_APP_ENV || "development",
    release: import.meta.env.VITE_SENTRY_RELEASE || "infracloud-inspection-mvp@dev",
    integrations: [Sentry.browserTracingIntegration(), Sentry.replayIntegration()],
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || 0.2),
    replaysSessionSampleRate: Number(
      import.meta.env.VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE || 0.05
    ),
    replaysOnErrorSampleRate: Number(
      import.meta.env.VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE || 1.0
    ),
    tracePropagationTargets: ["localhost", /^\//],
  });

  Sentry.setUser({
    id: sessionId,
    segment: "reviewer-session",
  });
  Sentry.setTag("service", "web");
}

export { Sentry };
