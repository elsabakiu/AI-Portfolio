import {
  VALID_CLASSES,
  VALID_DAMAGE_TYPES,
  VALID_MAIN_COMPONENT_CATEGORIES,
  VALID_MATERIALS,
  VALID_OBJECT_PART_CATEGORIES,
  VALID_OPTIONAL_REMARKS,
  VALID_QUANTITIES,
  VALID_STATUSES,
  YES_NO_OPTIONS,
} from "@config/fieldOptions";
import type { Proposal } from "@schemas/domain";

const NUMERIC_FIELDS = new Set([
  "ID",
  "Number",
  "Class",
  "Length",
  "Width",
  "Depth",
  "Estimated Remaining Cross Section",
  "Latitude",
  "Longitude",
  "Height (m)",
]);

const INTEGER_FIELDS = new Set(["ID", "Number"]);

const BOOLEAN_LIKE_FIELDS = new Set([
  "Closed",
  "Danger to life and health",
  "Immediate measures",
  "Current: Danger to life and limb",
]);

const ENUM_RULES: Record<string, readonly string[]> = {
  Status: VALID_STATUSES,
  Quantity: VALID_QUANTITIES,
  "Optional remark": VALID_OPTIONAL_REMARKS,
  "Damage Type": VALID_DAMAGE_TYPES,
  Material: VALID_MATERIALS,
  "Object Part Category": VALID_OBJECT_PART_CATEGORIES,
  "Main Component Category": VALID_MAIN_COMPONENT_CATEGORIES,
  Closed: YES_NO_OPTIONS,
  "Danger to life and health": YES_NO_OPTIONS,
  "Immediate measures": YES_NO_OPTIONS,
  "Current: Danger to life and limb": YES_NO_OPTIONS,
};

const DATE_FIELDS = new Set(["Created at"]);
const NULL_TOKENS = new Set(["", "-", "—", "null", "n/a", "na"]);
const BOOLEAN_TOKEN_MAP: Record<string, "Yes" | "No"> = {
  yes: "Yes",
  true: "Yes",
  y: "Yes",
  no: "No",
  false: "No",
  n: "No",
};

export interface NormalizedField {
  value: unknown;
  error: string | null;
}

export interface ValidationResult {
  proposal: Proposal;
  errors: Record<string, string>;
  isValid: boolean;
}

export function normalizeFieldValue(field: string, rawValue: unknown): NormalizedField {
  const original = typeof rawValue === "string" ? rawValue.trim() : rawValue;

  if (original === null || original === undefined) {
    return { value: null, error: null };
  }

  if (typeof original === "string" && NULL_TOKENS.has(original.toLowerCase())) {
    return { value: null, error: null };
  }

  if (NUMERIC_FIELDS.has(field)) {
    return normalizeNumericValue(field, original);
  }

  if (BOOLEAN_LIKE_FIELDS.has(field)) {
    return normalizeBooleanLikeValue(original);
  }

  if (DATE_FIELDS.has(field)) {
    return normalizeDateValue(original);
  }

  if (ENUM_RULES[field]) {
    return normalizeEnumValue(field, original);
  }

  if (typeof original === "string") {
    return { value: original, error: null };
  }

  return { value: original, error: null };
}

export function validateProposal(proposal: Proposal): ValidationResult {
  const nextProposal: Proposal = {};
  const errors: Record<string, string> = {};

  Object.entries(proposal || {}).forEach(([field, value]) => {
    const normalized = normalizeFieldValue(field, value);
    nextProposal[field] = normalized.value;
    if (normalized.error) {
      errors[field] = normalized.error;
    }
  });

  return {
    proposal: nextProposal,
    errors,
    isValid: Object.keys(errors).length === 0,
  };
}

function normalizeNumericValue(field: string, rawValue: unknown): NormalizedField {
  if (typeof rawValue === "number" && Number.isFinite(rawValue)) {
    if (INTEGER_FIELDS.has(field) && !Number.isInteger(rawValue)) {
      return { value: rawValue, error: "Must be a whole number." };
    }
    return { value: field === "Class" ? String(rawValue) : rawValue, error: null };
  }

  const parsed = Number(String(rawValue).replace(",", "."));
  if (!Number.isFinite(parsed)) {
    return { value: rawValue, error: "Must be a valid number." };
  }

  if (INTEGER_FIELDS.has(field) && !Number.isInteger(parsed)) {
    return { value: rawValue, error: "Must be a whole number." };
  }

  if (field === "Class" && !VALID_CLASSES.includes(String(parsed) as (typeof VALID_CLASSES)[number])) {
    return { value: parsed, error: "Class must be one of 1, 2, 3, or 4." };
  }

  if (field === "Class") {
    return { value: String(parsed), error: null };
  }

  if (field === "Latitude" && (parsed < -90 || parsed > 90)) {
    return { value: parsed, error: "Latitude must be between -90 and 90." };
  }

  if (field === "Longitude" && (parsed < -180 || parsed > 180)) {
    return { value: parsed, error: "Longitude must be between -180 and 180." };
  }

  return { value: parsed, error: null };
}

function normalizeBooleanLikeValue(rawValue: unknown): NormalizedField {
  if (typeof rawValue === "boolean") {
    return { value: rawValue ? "Yes" : "No", error: null };
  }

  if (typeof rawValue === "string") {
    const mapped = BOOLEAN_TOKEN_MAP[rawValue.toLowerCase()];
    if (mapped) {
      return { value: mapped, error: null };
    }
  }

  if (rawValue === "Yes" || rawValue === "No") {
    return { value: rawValue, error: null };
  }

  return { value: rawValue, error: "Use Yes or No." };
}

function normalizeDateValue(rawValue: unknown): NormalizedField {
  if (typeof rawValue !== "string") {
    return { value: rawValue, error: "Must be an ISO date string." };
  }

  const timestamp = Date.parse(rawValue);
  if (Number.isNaN(timestamp)) {
    return { value: rawValue, error: "Must be a valid date." };
  }

  return { value: new Date(timestamp).toISOString(), error: null };
}

function normalizeEnumValue(field: string, rawValue: unknown): NormalizedField {
  if (typeof rawValue !== "string") {
    return {
      value: rawValue,
      error: `Choose one of: ${ENUM_RULES[field].join(", ")}.`,
    };
  }

  const match = ENUM_RULES[field].find(
    (option) => option.toLowerCase() === rawValue.toLowerCase()
  );

  if (!match) {
    return {
      value: rawValue,
      error: `Choose one of: ${ENUM_RULES[field].join(", ")}.`,
    };
  }

  return { value: match, error: null };
}
