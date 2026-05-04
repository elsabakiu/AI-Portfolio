const ENVIRONMENT = process.env.NODE_ENV || "development";
import { redactSensitiveData } from "./redact.js";

function normalizeFields(fields = {}) {
  const normalized = { ...fields };

  if (normalized.requestId && !normalized.request_id) {
    normalized.request_id = normalized.requestId;
    delete normalized.requestId;
  }

  if (normalized.actorId && !normalized.actor_id) {
    normalized.actor_id = normalized.actorId;
    delete normalized.actorId;
  }

  if (normalized.workflowRunId && !normalized.workflow_run_id) {
    normalized.workflow_run_id = normalized.workflowRunId;
    delete normalized.workflowRunId;
  }

  if (normalized.suspicionId && !normalized.suspicion_id) {
    normalized.suspicion_id = normalized.suspicionId;
    delete normalized.suspicionId;
  }

  const error = normalized.error;
  if (error instanceof Error) {
    normalized.error_type = error.name;
    normalized.error_message = error.message;
    delete normalized.error;
  }

  return normalized;
}

function write(level, message, fields = {}) {
  const payload = {
    timestamp: new Date().toISOString(),
    level,
    service: "infracloud-review-api",
    environment: ENVIRONMENT,
    message,
    ...redactSensitiveData(normalizeFields(fields)),
  };

  const line = JSON.stringify(payload);
  if (level === "error") {
    console.error(line);
    return;
  }

  console.log(line);
}

export const logger = {
  info(message, fields) {
    write("info", message, fields);
  },
  warn(message, fields) {
    write("warn", message, fields);
  },
  error(message, fields) {
    write("error", message, fields);
  },
};
