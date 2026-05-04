import type { SampleCase } from "@schemas/domain";

export const sampleCases: SampleCase[] = [
  {
    suspicionId: 14401,
    title: "Crack Validation",
    summary: "Confirmed longitudinal crack in a dry concrete surface.",
    status: "ready",
    reviewState: "Ready to review",
    updateCount: 6,
    riskLevel: "Low risk",
    audioUrl: "/samples/test1.wav",
    recordUrl: "/records/test1_existing_record.json",
    scenario: "Validation and enrichment",
  },
  {
    suspicionId: 14402,
    title: "False Positive Rejection",
    summary: "Inspector rejects the suspected damage after on-site review.",
    status: "ready",
    reviewState: "Ready to review",
    updateCount: 3,
    riskLevel: "Medium risk",
    audioUrl: "/samples/test2.wav",
    recordUrl: "/records/test2_existing_record.json",
    scenario: "Incorrect detection review",
  },
  {
    suspicionId: 14403,
    title: "Material Conflict",
    summary: "Audio indicates steel corrosion instead of concrete damage.",
    status: "attention",
    reviewState: "Needs attention",
    updateCount: 5,
    riskLevel: "High attention",
    audioUrl: "/samples/test3.wav",
    recordUrl: "/records/test3_existing_record.json",
    scenario: "Material update and field correction",
  },
];

export function getSampleCaseById(id: string | number | undefined): SampleCase | undefined {
  return sampleCases.find((item) => String(item.suspicionId) === String(id));
}
