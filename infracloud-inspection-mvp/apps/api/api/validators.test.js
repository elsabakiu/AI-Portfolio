import { describe, expect, it } from "vitest";
import {
  validateDraftParams,
  validateExtractInput,
  validateProposalBody,
  validateWorkflowRunParams,
} from "./validators.js";
import { AppError } from "../lib/errors.js";

describe("API validators", () => {
  it("parses valid params and proposal bodies", () => {
    expect(validateDraftParams({ suspicionId: "14401" })).toEqual({ suspicionId: 14401 });
    expect(validateWorkflowRunParams({ runId: "run-123" })).toEqual({ runId: "run-123" });
    expect(
      validateProposalBody({
        suspicion_id: "14401",
        proposal: { Status: "Damage" },
      })
    ).toEqual({
      suspicionId: 14401,
      proposal: { Status: "Damage" },
    });
  });

  it("rejects malformed extraction input", () => {
    expect(() =>
      validateExtractInput({
        file: null,
        body: {},
      })
    ).toThrowError(AppError);

    expect(() =>
      validateExtractInput({
        file: { originalname: "sample.wav" },
        body: {
          suspicion_id: "14401",
          existing_record: "{bad json",
        },
      })
    ).toThrowError(AppError);
  });
});
