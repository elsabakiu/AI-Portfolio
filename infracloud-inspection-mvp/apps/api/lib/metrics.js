const DEFAULT_BUCKETS_MS = [50, 100, 250, 500, 1000, 2500, 5000, 10000];

function labelsKey(labels = {}) {
  return JSON.stringify(
    Object.entries(labels)
      .filter(([, value]) => value !== undefined && value !== null)
      .sort(([left], [right]) => left.localeCompare(right))
  );
}

function escapeLabelValue(value) {
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n");
}

function formatLabels(labels = {}) {
  const entries = Object.entries(labels).filter(([, value]) => value !== undefined && value !== null);
  if (entries.length === 0) return "";
  return `{${entries
    .map(([key, value]) => `${key}="${escapeLabelValue(value)}"`)
    .join(",")}}`;
}

export function createMetricsRegistry({ service, environment }) {
  const counters = new Map();
  const gauges = new Map();
  const histograms = new Map();

  function withBaseLabels(labels = {}) {
    return {
      service,
      environment,
      ...labels,
    };
  }

  function increment(name, labels = {}, value = 1) {
    const normalized = withBaseLabels(labels);
    const key = `${name}:${labelsKey(normalized)}`;
    const metric = counters.get(key) || { name, labels: normalized, value: 0 };
    metric.value += value;
    counters.set(key, metric);
  }

  function setGauge(name, value, labels = {}) {
    const normalized = withBaseLabels(labels);
    const key = `${name}:${labelsKey(normalized)}`;
    gauges.set(key, { name, labels: normalized, value });
  }

  function observe(name, value, labels = {}, buckets = DEFAULT_BUCKETS_MS) {
    const normalized = withBaseLabels(labels);
    const key = `${name}:${labelsKey(normalized)}`;
    const histogram =
      histograms.get(key) ||
      {
        name,
        labels: normalized,
        sum: 0,
        count: 0,
        buckets: buckets.map((bucket) => ({ le: bucket, value: 0 })),
      };

    histogram.sum += value;
    histogram.count += 1;
    for (const bucket of histogram.buckets) {
      if (value <= bucket.le) {
        bucket.value += 1;
      }
    }

    histograms.set(key, histogram);
  }

  function render() {
    const lines = [];

    for (const metric of counters.values()) {
      lines.push(`${metric.name}_total${formatLabels(metric.labels)} ${metric.value}`);
    }

    for (const metric of gauges.values()) {
      lines.push(`${metric.name}${formatLabels(metric.labels)} ${metric.value}`);
    }

    for (const metric of histograms.values()) {
      for (const bucket of metric.buckets) {
        lines.push(
          `${metric.name}_bucket${formatLabels({ ...metric.labels, le: bucket.le })} ${bucket.value}`
        );
      }
      lines.push(`${metric.name}_bucket${formatLabels({ ...metric.labels, le: "+Inf" })} ${metric.count}`);
      lines.push(`${metric.name}_sum${formatLabels(metric.labels)} ${metric.sum}`);
      lines.push(`${metric.name}_count${formatLabels(metric.labels)} ${metric.count}`);
    }

    return `${lines.join("\n")}\n`;
  }

  return {
    increment,
    setGauge,
    observe,
    render,
  };
}
