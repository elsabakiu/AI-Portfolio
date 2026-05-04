import { useMemo, useState } from "react";
import { formatValue, isChanged } from "@config/format";
import { getFieldConfig, type FieldConfig } from "@config/fieldOptions";
import type { Proposal, ReviewRecord } from "@schemas/domain";

interface ComparisonTableProps {
  existingRecord: ReviewRecord;
  proposedRecord: Proposal;
  confidenceByField?: Record<string, number | string>;
  validationErrors?: Record<string, string>;
  readOnlyFields?: string[];
  hiddenFields?: string[];
  showUpdatedOnly?: boolean;
  onToggleShowUpdatedOnly?: (value: boolean) => void;
  onChange: (key: string, rawValue: string) => void;
}

export function ComparisonTable({
  existingRecord,
  proposedRecord,
  confidenceByField = {},
  validationErrors = {},
  readOnlyFields = [],
  hiddenFields = [],
  showUpdatedOnly = true,
  onToggleShowUpdatedOnly,
  onChange,
}: ComparisonTableProps) {
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const readOnlyFieldSet = useMemo(() => new Set(readOnlyFields), [readOnlyFields]);
  const hiddenFieldSet = useMemo(() => new Set(hiddenFields), [hiddenFields]);
  const existingKeys = Object.keys(existingRecord || {}).filter((key) => !hiddenFieldSet.has(key));
  const proposedOnlyKeys = Object.keys(proposedRecord || {}).filter(
    (key) => !hiddenFieldSet.has(key) && !existingKeys.includes(key)
  );
  const sortedKeys = [...existingKeys, ...proposedOnlyKeys];
  const keys = showUpdatedOnly
    ? sortedKeys.filter((key) => isChanged(existingRecord[key], proposedRecord[key]))
    : sortedKeys;
  const updatedExistingCount = keys.filter(
    (key) => getChangeType(existingRecord[key], proposedRecord[key]) === "updated"
  ).length;
  const newValueCount = keys.filter(
    (key) => getChangeType(existingRecord[key], proposedRecord[key]) === "new"
  ).length;
  const lowConfidenceCount = keys.filter(
    (key) => getConfidenceTone(confidenceByField[key]) === "low"
  ).length;

  return (
    <section className="panel panel--table">
      <div className="panel__header">
        <div>
          <h2>{showUpdatedOnly ? "Updated Fields" : "All Damage Fields"}</h2>
          <p>Review the proposed InfraCloud updates against the current damage record.</p>
          <div className="table-summary">
            <span>{keys.length} updates detected</span>
            <span>{updatedExistingCount} changed values</span>
            <span>{newValueCount} new values</span>
            {lowConfidenceCount > 0 && <span>{lowConfidenceCount} low-confidence rows</span>}
          </div>
        </div>
        <div className="view-toggle" role="tablist" aria-label="Field view mode">
          <button
            className={`view-toggle__button ${showUpdatedOnly ? "view-toggle__button--active" : ""}`}
            onClick={() => onToggleShowUpdatedOnly?.(true)}
            type="button"
          >
            Updated Only
          </button>
          <button
            className={`view-toggle__button ${!showUpdatedOnly ? "view-toggle__button--active" : ""}`}
            onClick={() => onToggleShowUpdatedOnly?.(false)}
            type="button"
          >
            All Fields
          </button>
        </div>
      </div>
      {keys.length === 0 ? (
        <div className="table-empty-state">
          <p>No field updates were proposed for this record.</p>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Type</th>
                <th>Existing</th>
                <th>Proposed</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((key) => {
                const changed = isChanged(existingRecord[key], proposedRecord[key]);
                const hasError = Boolean(validationErrors[key]);
                const isReadOnly = readOnlyFieldSet.has(key);
                const fieldConfig = getFieldConfig(key);
                const changeType = getChangeType(existingRecord[key], proposedRecord[key]);
                return (
                  <tr
                    key={key}
                    className={`${changed ? "is-changed" : ""} ${hasError ? "is-invalid" : ""}`.trim()}
                  >
                    <td>{key}</td>
                    <td>
                      <ChangeTypeBadge type={changeType} />
                    </td>
                    <td>{formatValue(existingRecord[key])}</td>
                    <td>
                      {isReadOnly ? (
                        <div className="table-display-cell">
                          <div className="table-static-value">{formatValue(proposedRecord[key])}</div>
                        </div>
                      ) : editingKey === key ? (
                        <div className="table-edit-cell">
                          <FieldEditor
                            fieldConfig={fieldConfig}
                            hasError={hasError}
                            onCancel={() => setEditingKey(null)}
                            onCommit={(value) => {
                              onChange(key, value);
                              setEditingKey(null);
                            }}
                            value={proposedRecord[key]}
                          />
                          {fieldConfig.helper && <p className="table-helper">{fieldConfig.helper}</p>}
                          {hasError && <p className="table-error">{validationErrors[key]}</p>}
                        </div>
                      ) : (
                        <div className="table-display-cell">
                          <button
                            className={`table-value-button ${changed ? "table-value-button--changed" : ""} ${hasError ? "table-value-button--invalid" : ""}`.trim()}
                            onClick={() => setEditingKey(key)}
                            type="button"
                          >
                            {formatValue(proposedRecord[key])}
                          </button>
                          {hasError && <p className="table-error">{validationErrors[key]}</p>}
                        </div>
                      )}
                    </td>
                    <td>
                      <ConfidenceBadge value={confidenceByField[key]} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

interface FieldEditorProps {
  fieldConfig: FieldConfig;
  value: unknown;
  hasError: boolean;
  onCommit: (value: string) => void;
  onCancel: () => void;
}

function FieldEditor({ fieldConfig, value, hasError, onCommit, onCancel }: FieldEditorProps) {
  const inputClassName = `table-input ${hasError ? "table-input--invalid" : ""}`;
  const normalizedValue = value === null || value === undefined ? "" : String(value);

  if (fieldConfig.editor === "select") {
    return (
      <select
        autoFocus
        className={inputClassName}
        defaultValue={normalizedValue}
        onBlur={(event) => onCommit(event.target.value)}
        onChange={(event) => onCommit(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onCancel();
          }
        }}
      >
        <option value="">Clear value</option>
        {fieldConfig.options?.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }

  return (
    <input
      autoFocus
      className={inputClassName}
      defaultValue={normalizedValue === "—" ? "" : normalizedValue}
      inputMode={fieldConfig.editor === "number" ? "decimal" : undefined}
      onBlur={(event) => onCommit(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.currentTarget.blur();
        }
        if (event.key === "Escape") {
          onCancel();
        }
      }}
    />
  );
}

function ConfidenceBadge({ value }: { value: number | string | undefined }) {
  const tone = getConfidenceTone(value);
  const label = getConfidenceLabel(value);
  return <span className={`confidence-pill confidence-pill--${tone}`}>{label}</span>;
}

function ChangeTypeBadge({ type }: { type: string }) {
  return <span className={`change-pill change-pill--${type}`}>{getChangeTypeLabel(type)}</span>;
}

function getConfidenceTone(value: unknown) {
  const score = toConfidenceScore(value);

  if (score === null) return "neutral";
  if (score < 0.65) return "low";
  if (score < 0.85) return "medium";
  return "high";
}

function getConfidenceLabel(value: unknown) {
  const score = toConfidenceScore(value);
  if (score === null) return "—";

  const percent = `${Math.round(score * 100)}%`;
  const tone = getConfidenceTone(score);
  if (tone === "high") return percent;
  if (tone === "medium") return `Medium ${percent}`;
  return `Low ${percent}`;
}

function toConfidenceScore(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  const parsed = Number(value);
  if (Number.isFinite(parsed)) {
    return parsed;
  }

  return null;
}

function getChangeType(existing: unknown, proposed: unknown) {
  const left = formatValue(existing);
  const right = formatValue(proposed);

  if (left === right) return "unchanged";
  if (left === "—" && right !== "—") return "new";
  if (left !== "—" && right === "—") return "cleared";
  return "updated";
}

function getChangeTypeLabel(type: string) {
  if (type === "new") return "New";
  if (type === "cleared") return "Cleared";
  if (type === "updated") return "Changed";
  return "Unchanged";
}
