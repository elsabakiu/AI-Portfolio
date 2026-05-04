import { describe, expect, it } from "vitest";
import { diffRecords } from "./diff.js";

describe("diffRecords", () => {
  it("returns changed and new fields", () => {
    const diff = diffRecords(
      { Status: "Suspicion", Width: null },
      { Status: "Damage", Width: 2, Length: 30 }
    );

    expect(diff).toEqual([
      { field: "Status", before: "Suspicion", after: "Damage" },
      { field: "Width", before: null, after: 2 },
      { field: "Length", before: null, after: 30 },
    ]);
  });

  it("ignores unchanged values", () => {
    expect(diffRecords({ Status: "Damage" }, { Status: "Damage" })).toEqual([]);
  });
});
