export class AppError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.name = "AppError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function toErrorResponse({ code, message, requestId, details }) {
  return {
    ok: false,
    error: {
      code,
      message,
      requestId,
      details,
    },
  };
}

export function toSuccessResponse(data, requestId) {
  return {
    ok: true,
    data,
    meta: { requestId },
  };
}
