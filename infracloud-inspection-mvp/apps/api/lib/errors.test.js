import { describe, expect, it } from "vitest";
import { AppError, toErrorResponse, toSuccessResponse } from "./errors.js";

describe("error mapping", () => {
  it("creates a typed AppError", () => {
    const error = new AppError(400, "INVALID_INPUT", "Bad input", { field: "status" });

    expect(error).toBeInstanceOf(Error);
    expect(error.status).toBe(400);
    expect(error.code).toBe("INVALID_INPUT");
    expect(error.details).toEqual({ field: "status" });
  });

  it("maps success and failure payloads", () => {
    expect(toSuccessResponse({ ok: "yes" }, "req-1")).toEqual({
      ok: true,
      data: { ok: "yes" },
      meta: { requestId: "req-1" },
    });

    expect(
      toErrorResponse({
        code: "BROKEN",
        message: "Something broke",
        requestId: "req-2",
        details: { reason: "boom" },
      })
    ).toEqual({
      ok: false,
      error: {
        code: "BROKEN",
        message: "Something broke",
        requestId: "req-2",
        details: { reason: "boom" },
      },
    });
  });
});
