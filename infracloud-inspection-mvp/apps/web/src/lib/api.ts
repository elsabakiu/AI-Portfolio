import { Sentry } from "../instrument";
import type {
  ApiFailure,
  ApiResponse,
  DraftPayload,
  ExtractionResult,
  Proposal,
  SaveDraftResult,
  SendResult,
  WorkflowRunRecord,
} from "@schemas/domain";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  code: string;
  requestId?: string;
  details?: unknown;
  status: number;

  constructor(status: number, payload: ApiFailure["error"]) {
    super(payload.message || "Request failed.");
    this.name = "ApiError";
    this.status = status;
    this.code = payload.code;
    this.requestId = payload.requestId;
    this.details = payload.details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, init);
    const text = await response.text();
    let payload: ApiResponse<T> | null = null;

    try {
      payload = text ? (JSON.parse(text) as ApiResponse<T>) : null;
    } catch {
      payload = null;
    }

    if (!response.ok || !payload?.ok) {
      const fallback: ApiFailure["error"] = {
        code: payload?.ok ? "UNKNOWN_ERROR" : payload?.error?.code || "UNEXPECTED_RESPONSE",
        message:
          payload?.ok
            ? "Request failed."
            : payload?.error?.message ||
              `Request failed with status ${response.status}. The server returned a non-JSON response.`,
      };
      const error = new ApiError(
        response.status,
        payload?.ok ? fallback : payload?.error || fallback
      );
      Sentry.withScope((scope) => {
        scope.setTag("service", "web");
        scope.setTag("api_path", path);
        scope.setTag("api_status", String(response.status));
        scope.setLevel("error");
        scope.setContext("api_error", {
          path,
          status: response.status,
          code: error.code,
          request_id: error.requestId,
          details: error.details,
          response_preview: text.slice(0, 200),
        });
        Sentry.captureException(error);
      });
      throw error;
    }

    return payload.data;
  } catch (error) {
    if (!(error instanceof ApiError)) {
      Sentry.withScope((scope) => {
        scope.setTag("service", "web");
        scope.setTag("api_path", path);
        scope.setLevel("error");
        Sentry.captureException(error instanceof Error ? error : new Error(String(error)));
      });
    }
    throw error;
  }
}

export function getDraft(suspicionId: number): Promise<DraftPayload> {
  return request<DraftPayload>(`/draft/${suspicionId}`);
}

export function extractInspection(formData: FormData): Promise<ExtractionResult> {
  return request<ExtractionResult>("/extract", {
    method: "POST",
    body: formData,
  });
}

export function getWorkflowRun(runId: string): Promise<WorkflowRunRecord> {
  return request<WorkflowRunRecord>(`/extractions/${runId}`);
}

export function saveDraft(suspicionId: number, proposal: Proposal): Promise<SaveDraftResult> {
  return request<SaveDraftResult>("/save-draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ suspicion_id: suspicionId, proposal }),
  });
}

export function sendToInfraCloud(suspicionId: number, proposal: Proposal): Promise<SendResult> {
  return request<SendResult>("/send-to-infracloud", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ suspicion_id: suspicionId, proposal }),
  });
}
