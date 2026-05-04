import { AlertTriangle, BadgeCheck, Brain, GitCompareArrows, Save, Send } from "lucide-react";
import type { Conflict } from "@schemas/domain";
import { formatValue } from "@config/format";

interface ReviewSummaryPanelProps {
  intent?: string | null;
  conflicts?: Conflict[];
  confidence?: Record<string, number | string>;
  langsmithRunId?: string;
  lastSavedAt?: string | null;
  lastSentAt?: string | null;
}

export function ReviewSummaryPanel({
  intent,
  conflicts: updates = [],
  confidence = {},
  langsmithRunId,
  lastSavedAt,
  lastSentAt,
}: ReviewSummaryPanelProps) {
  const confidenceEntries = Object.entries(confidence || {}).sort((left, right) =>
    left[0].localeCompare(right[0])
  );

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>Review Summary</h2>
          <p>Decision signals, update review, and audit metadata for this extraction.</p>
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <div className="summary-card__title">
            <BadgeCheck size={16} />
            <span>Intent</span>
          </div>
          <strong>{intent || "—"}</strong>
        </div>

        <div className="summary-card">
          <div className="summary-card__title">
            <GitCompareArrows size={16} />
            <span>Conflicts</span>
          </div>
          <strong>{updates.length}</strong>
        </div>

        <div className="summary-card">
          <div className="summary-card__title">
            <Save size={16} />
            <span>Last Draft Save</span>
          </div>
          <strong>{lastSavedAt || "Not saved yet"}</strong>
        </div>

        <div className="summary-card">
          <div className="summary-card__title">
            <Send size={16} />
            <span>Last Send</span>
          </div>
          <strong>{lastSentAt || "Not sent yet"}</strong>
        </div>
      </div>

      {langsmithRunId && (
        <p className="summary-meta">
          LangSmith run: <span className="mono">{langsmithRunId}</span>
        </p>
      )}

      {updates.length > 0 && (
        <div className="summary-section">
          <h3>
            <AlertTriangle size={16} />
            Conflicts to review
          </h3>
          <div className="summary-list">
            {updates.map((update, index) => (
              <div className="summary-list__item" key={`${update.field}-${index}`}>
                <strong>{update.field}</strong>
                <p>
                  Existing: {formatValue(update.existing_value)} | Extracted: {formatValue(update.extracted_value)}
                </p>
                <span>{update.proposed_resolution}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {confidenceEntries.length > 0 && (
        <div className="summary-section">
          <h3>
            <Brain size={16} />
            Confidence
          </h3>
          <div className="summary-list summary-list--compact">
            {confidenceEntries.map(([key, value]) => (
              <div className="summary-list__item" key={key}>
                <strong>{key}</strong>
                <span>{formatValue(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
