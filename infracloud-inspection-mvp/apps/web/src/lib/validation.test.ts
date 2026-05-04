import { describe, expect, it } from "vitest";
import { normalizeFieldValue, validateProposal } from "./validation";

describe("validation rules", () => {
  it("normalizes boolean-like values from booleans and strings", () => {
    expect(normalizeFieldValue("Danger to life and health", true)).toEqual({
      value: "Yes",
      error: null,
    });
    expect(normalizeFieldValue("Immediate measures", "false")).toEqual({
      value: "No",
      error: null,
    });
  });

  it("normalizes enum values case-insensitively", () => {
    expect(normalizeFieldValue("Status", "damage")).toEqual({
      value: "Damage",
      error: null,
    });
  });

  it("returns numeric and enum validation errors", () => {
    expect(normalizeFieldValue("Class", "9")).toEqual({
      value: 9,
      error: "Class must be one of 1, 2, 3, or 4.",
    });

    expect(normalizeFieldValue("Latitude", "181")).toEqual({
      value: 181,
      error: "Latitude must be between -90 and 90.",
    });
  });

  it("validates and normalizes a proposal as a whole", () => {
    const result = validateProposal({
      Status: "damage",
      Class: "2",
      Closed: false,
      "Created at": "2026-03-23",
    });

    expect(result.isValid).toBe(true);
    expect(result.proposal).toMatchObject({
      Status: "Damage",
      Class: "2",
      Closed: "No",
    });
    expect(result.proposal["Created at"]).toContain("2026-03-23T00:00:00.000Z");
  });

  it("surfaces invalid enum and boolean values", () => {
    const result = validateProposal({
      Status: "broken",
      Closed: "maybe",
    });

    expect(result.isValid).toBe(false);
    expect(result.errors.Status).toContain("Choose one of");
    expect(result.errors.Closed).toBe("Use Yes or No.");
  });
});
