// @vitest-environment node

import httpMocks from "node-mocks-http";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createDraftsRouter } from "./routes/drafts.js";
import { createExtractionRouter } from "./routes/extraction.js";
import { createSubmissionsRouter } from "./routes/submissions.js";
import { createErrorHandlerMiddleware } from "./middleware/errors.js";
import { createMetricsRegistry } from "../lib/metrics.js";
import { AppError } from "../lib/errors.js";

function createContext() {
  const metrics = createMetricsRegistry({
    service: "test-api",
    environment: "test",
  });

  const errorMiddleware = createErrorHandlerMiddleware(metrics);
  const extractionService = {
    runExtraction: vi.fn(async ({ suspicionId }) => ({
      workflow_run_id: "workflow-run-1",
      suspicion_id: String(suspicionId),
      intent: "VALIDATE_DAMAGE",
      transcript: "Schaden bestaetigt.",
      simulated_infracloud_payload: {
        ID: suspicionId,
        Status: "Damage",
      },
    })),
  };

  let savedDraft = null;

  const draftsService = {
    getLatestDraftBySuspicionId: vi.fn(async () => savedDraft),
    saveDraft: vi.fn(async ({ suspicionId, proposal }) => {
      savedDraft = {
        suspicion_id: suspicionId,
        proposal,
        savedAt: "2026-03-23T10:30:00.000Z",
        workflow_run_id: "workflow-run-1",
        transcript: "Schaden bestaetigt.",
      };
      return savedDraft;
    }),
  };

  const submissionsService = {
    createSubmission: vi.fn(async () => ({
      sentAt: "2026-03-23T11:00:00.000Z",
      mode: "mock-send",
    })),
  };

  return {
    metrics,
    errorMiddleware,
    extractionService,
    draftsService,
    submissionsService,
  };
}

async function invokeRoute(router, { method, path, reqOptions, errorMiddleware }) {
  const layer = router.stack.find(
    (entry) => entry.route?.path === path && entry.route.methods[method]
  );

  if (!layer) {
    throw new Error(`Route ${method.toUpperCase()} ${path} not found.`);
  }

  const req = httpMocks.createRequest({
    method: method.toUpperCase(),
    url: path,
    ...reqOptions,
  });
  req.requestId = req.requestId || "req-test-1";
  req.actor = req.actor || { userId: "local-dev-user", role: "reviewer" };

  const res = httpMocks.createResponse({
    eventEmitter: (await import("node:events")).EventEmitter,
  });

  let capturedError = null;
  for (const handlerLayer of layer.route.stack) {
    await new Promise((resolve, reject) => {
      const maybePromise = handlerLayer.handle(req, res, (error) => {
        if (error) {
          capturedError = error;
        }
        resolve(undefined);
      });

      if (maybePromise?.then) {
        maybePromise.then(resolve).catch(reject);
      } else if (handlerLayer.handle.length < 3) {
        resolve(undefined);
      }
    });

    if (capturedError) break;
  }

  if (capturedError) {
    errorMiddleware(capturedError, req, res);
  }

  return res;
}

describe("route integration", () => {
  let context;

  beforeEach(() => {
    context = createContext();
  });

  it("returns extraction results for a valid request", async () => {
    const router = createExtractionRouter({
      extractionService: context.extractionService,
      config: { uploadFileSizeLimitBytes: 15 * 1024 * 1024 },
    });

    const response = await invokeRoute(router, {
      method: "post",
      path: "/extract",
      reqOptions: {
        actor: { userId: "reviewer-1", role: "reviewer" },
        body: {
          suspicion_id: "14401",
          existing_record: JSON.stringify({ ID: 14401, Status: "Suspicion" }),
        },
        file: {
          originalname: "sample.wav",
          mimetype: "audio/wav",
          buffer: Buffer.from("hello"),
        },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(response.statusCode).toBe(200);
    expect(response._getJSONData().data.workflow_run_id).toBe("workflow-run-1");
  });

  it("returns a validation error for invalid extraction input", async () => {
    const router = createExtractionRouter({
      extractionService: context.extractionService,
      config: { uploadFileSizeLimitBytes: 15 * 1024 * 1024 },
    });

    const response = await invokeRoute(router, {
      method: "post",
      path: "/extract",
      reqOptions: {
        actor: { userId: "reviewer-1", role: "reviewer" },
        body: {
          suspicion_id: "14401",
        },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(response.statusCode).toBe(400);
    expect(response._getJSONData().error.code).toBe("MISSING_AUDIO_FILE");
  });

  it("maps upstream extraction failures", async () => {
    context.extractionService.runExtraction.mockRejectedValueOnce(
      new AppError(502, "UPSTREAM_UNAVAILABLE", "Workflow unavailable", {
        stage: "workflow_execution",
        suspicion_id: 14401,
      })
    );

    const router = createExtractionRouter({
      extractionService: context.extractionService,
      config: { uploadFileSizeLimitBytes: 15 * 1024 * 1024 },
    });

    const response = await invokeRoute(router, {
      method: "post",
      path: "/extract",
      reqOptions: {
        actor: { userId: "reviewer-1", role: "reviewer" },
        body: {
          suspicion_id: "14401",
          existing_record: JSON.stringify({ ID: 14401, Status: "Suspicion" }),
        },
        file: {
          originalname: "sample.wav",
          mimetype: "audio/wav",
          buffer: Buffer.from("hello"),
        },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(response.statusCode).toBe(502);
    expect(response._getJSONData().error.code).toBe("UPSTREAM_UNAVAILABLE");
  });

  it("supports draft save and resume", async () => {
    const router = createDraftsRouter({
      draftsService: context.draftsService,
    });

    const saveResponse = await invokeRoute(router, {
      method: "post",
      path: "/save-draft",
      reqOptions: {
        actor: { userId: "approver-1", role: "approver" },
        body: {
          suspicion_id: 14401,
          proposal: { ID: 14401, Status: "Damage" },
        },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(saveResponse.statusCode).toBe(200);
    expect(saveResponse._getJSONData().data.savedAt).toBe("2026-03-23T10:30:00.000Z");

    const loadResponse = await invokeRoute(router, {
      method: "get",
      path: "/draft/:suspicionId",
      reqOptions: {
        actor: { userId: "reviewer-1", role: "reviewer" },
        params: { suspicionId: "14401" },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(loadResponse.statusCode).toBe(200);
    expect(loadResponse._getJSONData().data.proposal.Status).toBe("Damage");
    expect(loadResponse._getJSONData().data.transcript).toBe("Schaden bestaetigt.");
  });

  it("supports the submission flow", async () => {
    const router = createSubmissionsRouter({
      submissionsService: context.submissionsService,
    });

    const response = await invokeRoute(router, {
      method: "post",
      path: "/send-to-infracloud",
      reqOptions: {
        actor: { userId: "approver-1", role: "approver" },
        body: {
          suspicion_id: 14401,
          proposal: { ID: 14401, Status: "Damage" },
        },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(response.statusCode).toBe(200);
    expect(response._getJSONData().data.mode).toBe("mock-send");
  });

  it("blocks reviewers from saving drafts", async () => {
    const router = createDraftsRouter({
      draftsService: context.draftsService,
    });

    const response = await invokeRoute(router, {
      method: "post",
      path: "/save-draft",
      reqOptions: {
        actor: { userId: "reviewer-1", role: "reviewer" },
        body: {
          suspicion_id: 14401,
          proposal: { ID: 14401, Status: "Damage" },
        },
      },
      errorMiddleware: context.errorMiddleware,
    });

    expect(response.statusCode).toBe(403);
    expect(response._getJSONData().error.code).toBe("FORBIDDEN");
  });
});
