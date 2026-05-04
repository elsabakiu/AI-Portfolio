import { AlertTriangle, CheckCircle2, FileCheck2, Send } from "lucide-react";
import { StatusBadge } from "./StatusBadge";

interface ReviewSummaryStripProps {
  intent?: string | null;
  updatedCount: number;
  lowConfidenceCount: number;
  validationCount: number;
  draftSaved: boolean;
  approved: boolean;
  sent: boolean;
}

export function ReviewSummaryStrip({
  intent,
  updatedCount,
  lowConfidenceCount,
  validationCount,
  draftSaved,
  approved,
  sent,
}: ReviewSummaryStripProps) {
  return (
    <section className="review-strip panel">
      <div className="review-strip__header">
        <div>
          <h2>Review Overview</h2>
          <p>Use this summary to decide what needs attention before approval and send.</p>
        </div>
        <StatusBadge tone={intentTone[intent || ""] || "neutral"}>{intent || "No intent"}</StatusBadge>
      </div>

      <div className="review-strip__grid">
        <div className="review-strip__item">
          <div className="review-strip__label">
            <FileCheck2 size={15} />
            <span>Updates</span>
          </div>
          <strong>{updatedCount}</strong>
        </div>
        <div className="review-strip__item">
          <div className="review-strip__label">
            <AlertTriangle size={15} />
            <span>Low Confidence</span>
          </div>
          <strong>{lowConfidenceCount}</strong>
        </div>
        <div className="review-strip__item">
          <div className="review-strip__label">
            <CheckCircle2 size={15} />
            <span>Approval</span>
          </div>
          <strong>{approved ? "Approved" : validationCount > 0 ? "Needs review" : "Ready"}</strong>
        </div>
        <div className="review-strip__item">
          <div className="review-strip__label">
            <Send size={15} />
            <span>Submission</span>
          </div>
          <strong>{sent ? "Sent" : draftSaved ? "Draft saved" : "Not saved"}</strong>
        </div>
      </div>
    </section>
  );
}

const intentTone: Record<string, string> = {
  VALIDATE_DAMAGE: "success",
  REJECT_DAMAGE: "warning",
  UPDATE_FIELD: "primary",
};
