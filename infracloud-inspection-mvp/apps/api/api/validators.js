import { AppError } from "../lib/errors.js";

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseSuspicionId(value, fieldName = "suspicion_id") {
  const normalized = String(value ?? "").trim();
  if (!/^\d+$/.test(normalized)) {
    throw new AppError(400, "INVALID_SUSPICION_ID", `${fieldName} must be a numeric ID.`);
  }

  return Number(normalized);
}

export function validateDraftParams(params) {
  return {
    suspicionId: parseSuspicionId(params.suspicionId, "suspicionId"),
  };
}

export function validateWorkflowRunParams(params) {
  const runId = String(params.runId ?? "").trim();
  if (!runId) {
    throw new AppError(400, "INVALID_WORKFLOW_RUN_ID", "runId must be provided.");
  }

  return {
    runId,
  };
}

export function validateProposalBody(body) {
  const suspicionId = parseSuspicionId(body?.suspicion_id);

  if (!isPlainObject(body?.proposal)) {
    throw new AppError(
      400,
      "INVALID_PROPOSAL",
      "proposal must be a JSON object containing the reviewed record."
    );
  }

  return {
    suspicionId,
    proposal: body.proposal,
  };
}

export function validateExtractInput(req) {
  if (!req.file) {
    throw new AppError(400, "MISSING_AUDIO_FILE", "Missing audio_file upload.");
  }

  const suspicionId = parseSuspicionId(req.body?.suspicion_id);
  const existingRecordRaw = req.body?.existing_record;

  if (typeof existingRecordRaw !== "string" || !existingRecordRaw.trim()) {
    throw new AppError(
      400,
      "MISSING_EXISTING_RECORD",
      "existing_record must be provided as a JSON string."
    );
  }

  try {
    JSON.parse(existingRecordRaw);
  } catch (error) {
    throw new AppError(400, "INVALID_EXISTING_RECORD", "existing_record is not valid JSON.", {
      reason: error instanceof Error ? error.message : String(error),
    });
  }

  return {
    suspicionId,
    existingRecord: JSON.parse(existingRecordRaw),
    existingRecordRaw,
  };
}
