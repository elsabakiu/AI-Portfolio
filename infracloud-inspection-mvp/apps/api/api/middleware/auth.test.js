import { describe, expect, it, vi } from "vitest";
import { AppError } from "../../lib/errors.js";
import { authorizeRoles, createAuthMiddleware } from "./auth.js";

function createReq(headers = {}) {
  return {
    headers,
  };
}

describe("auth middleware", () => {
  it("allows header-based auth in development-like mode", () => {
    const middleware = createAuthMiddleware({
      authMode: "headers",
    });
    const req = createReq({
      "x-user-id": "approver-1",
      "x-user-role": "approver",
    });
    const next = vi.fn();

    middleware(req, {}, next);

    expect(req.actor).toMatchObject({
      userId: "approver-1",
      role: "approver",
      authenticated: true,
    });
    expect(next).toHaveBeenCalledWith();
  });

  it("requires a valid bearer token when configured", () => {
    const middleware = createAuthMiddleware({
      authMode: "bearer",
      authTokens: [{ token: "good-token", userId: "admin-1", role: "admin", displayName: "Admin" }],
    });
    const next = vi.fn();

    middleware(createReq({ authorization: "Bearer bad-token" }), {}, next);
    const error = next.mock.calls[0][0];

    expect(error).toBeInstanceOf(AppError);
    expect(error.status).toBe(401);
  });

  it("enforces role-based authorization", () => {
    const middleware = authorizeRoles(["approver", "admin"]);
    const next = vi.fn();

    middleware({ actor: { role: "reviewer" } }, {}, next);
    const error = next.mock.calls[0][0];
    expect(error).toBeInstanceOf(AppError);
    expect(error.status).toBe(403);
  });
});
