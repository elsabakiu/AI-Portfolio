import { ArrowRight, FileAudio, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import type { SampleCase } from "@schemas/domain";
import { StatusBadge } from "./StatusBadge";

interface CaseCardProps {
  item: SampleCase;
}

export function CaseCard({ item }: CaseCardProps) {
  const tone = item.status === "attention" ? "warning" : "primary";
  const riskTone = item.status === "attention" ? "warning" : "success";

  return (
    <Link className="case-card" to={`/review/${item.suspicionId}`}>
      <div className="case-card__icon">
        {item.status === "attention" ? <ShieldAlert size={18} /> : <FileAudio size={18} />}
      </div>
      <div className="case-card__body">
        <div className="case-card__meta">
          <span className="mono">#{item.suspicionId}</span>
          <StatusBadge tone={tone}>{item.scenario}</StatusBadge>
          <StatusBadge tone={riskTone}>{item.reviewState}</StatusBadge>
        </div>
        <h3>{item.title}</h3>
        <p>{item.summary}</p>
        <div className="case-card__signals">
          <span>{item.updateCount} proposed updates</span>
          <span>{item.riskLevel}</span>
        </div>
      </div>
      <ArrowRight size={18} className="case-card__arrow" />
    </Link>
  );
}
