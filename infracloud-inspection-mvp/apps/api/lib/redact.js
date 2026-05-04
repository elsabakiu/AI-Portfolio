const SENSITIVE_KEY_PATTERN =
  /(authorization|api[_-]?key|token|secret|password|dsn|cookie|set-cookie|base64)/i;

function redactString(value) {
  if (typeof value !== "string") return value;
  if (value.length <= 8) return "[REDACTED]";
  return `${value.slice(0, 4)}...[REDACTED]`;
}

export function redactSensitiveData(value, parentKey = "") {
  if (value === null || value === undefined) return value;

  if (Array.isArray(value)) {
    return value.map((item) => redactSensitiveData(item, parentKey));
  }

  if (typeof value === "object") {
    const output = {};
    for (const [key, nestedValue] of Object.entries(value)) {
      if (SENSITIVE_KEY_PATTERN.test(key)) {
        output[key] = typeof nestedValue === "string" ? redactString(nestedValue) : "[REDACTED]";
        continue;
      }
      output[key] = redactSensitiveData(nestedValue, key);
    }
    return output;
  }

  if (typeof value === "string" && SENSITIVE_KEY_PATTERN.test(parentKey)) {
    return redactString(value);
  }

  return value;
}
