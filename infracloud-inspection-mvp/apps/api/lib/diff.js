export function diffRecords(previous = {}, next = {}) {
  const keys = new Set([...Object.keys(previous || {}), ...Object.keys(next || {})]);
  const changes = [];

  for (const key of keys) {
    const before = previous?.[key] ?? null;
    const after = next?.[key] ?? null;

    if (JSON.stringify(before) === JSON.stringify(after)) {
      continue;
    }

    changes.push({
      field: key,
      before,
      after,
    });
  }

  return changes;
}
