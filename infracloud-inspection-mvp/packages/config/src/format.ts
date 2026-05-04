export function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export function isChanged(leftValue: unknown, rightValue: unknown): boolean {
  return formatValue(leftValue) !== formatValue(rightValue);
}

export function titleFromKey(key: string): string {
  return key.replace(/_/g, " ");
}
