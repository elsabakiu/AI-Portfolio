import { describe, expect, it } from "vitest";
import { redactSensitiveData } from "./redact.js";

describe("redactSensitiveData", () => {
  it("redacts sensitive keys recursively", () => {
    const output = redactSensitiveData({
      authorization: "Bearer super-secret-token",
      nested: {
        OPENAI_API_KEY: "sk-123456789",
        safe: "keep-me",
      },
      audio: {
        base64: "AAAAABBBBBCCCCCDDDD",
      },
    });

    expect(output.authorization).toContain("[REDACTED]");
    expect(output.nested.OPENAI_API_KEY).toContain("[REDACTED]");
    expect(output.nested.safe).toBe("keep-me");
    expect(output.audio.base64).toContain("[REDACTED]");
  });
});
