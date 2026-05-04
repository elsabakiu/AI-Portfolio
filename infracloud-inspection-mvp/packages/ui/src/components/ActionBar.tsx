import { CheckCircle2, Send } from "lucide-react";

interface ActionBarProps {
  onSaveAndApprove: () => void | Promise<void>;
  onSend: () => void | Promise<void>;
  sending: boolean;
  sent: boolean;
  hasValidationErrors: boolean;
  validationCount: number;
  draftSaved: boolean;
}

export function ActionBar({
  onSaveAndApprove,
  onSend,
  sending,
  sent,
  hasValidationErrors,
  validationCount,
  draftSaved,
}: ActionBarProps) {
  const nextStep = hasValidationErrors
    ? "Resolve validation"
    : draftSaved
      ? "Send to InfraCloud"
      : "Save";
  const saveLabel = draftSaved ? "Saved" : "Save";

  return (
    <div className="action-bar">
      {!sent && (
        <div className="action-bar__status">
          <span className="action-bar__step">Next: {nextStep}</span>
          {hasValidationErrors && (
            <span className="action-bar__status--error">
              Fix {validationCount} invalid field{validationCount === 1 ? "" : "s"} before approval.
            </span>
          )}
          {draftSaved && <span>Draft saved.</span>}
        </div>
      )}
      <div className="action-bar__actions">
        <button
          className={`button ${!draftSaved && !hasValidationErrors ? "" : "button--outline"}`}
          disabled={draftSaved || sent || hasValidationErrors}
          onClick={onSaveAndApprove}
          type="button"
        >
          <CheckCircle2 size={16} />
          {saveLabel}
        </button>
        <button
          className={`button ${draftSaved && !sent ? "" : "button--outline"}`}
          disabled={!draftSaved || sending || sent || hasValidationErrors}
          onClick={onSend}
          type="button"
        >
          <Send size={16} />
          {sending ? "Sending..." : sent ? "Sent" : "Send to InfraCloud"}
        </button>
      </div>
    </div>
  );
}
