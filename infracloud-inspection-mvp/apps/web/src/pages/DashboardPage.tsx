import { AudioLines, ClipboardList } from "lucide-react";
import { CaseCard } from "@ui/components/CaseCard";
import { sampleCases } from "../data/sampleCases";

export function DashboardPage() {
  const attentionCount = sampleCases.filter((item) => item.status === "attention").length;
  const totalUpdates = sampleCases.reduce((sum, item) => sum + (item.updateCount || 0), 0);

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="topbar__brand">
          <div className="topbar__logo">
            <ClipboardList size={16} />
          </div>
          <div>
            <h1>InfraCloud Inspection Review</h1>
            <p>Audio-driven extraction review workspace</p>
          </div>
        </div>
        <div className="topbar__stats">
          <span>
            <AudioLines size={14} />
            {sampleCases.length} sample cases
          </span>
          <span>{attentionCount} need attention</span>
          <span>{totalUpdates} proposed updates</span>
        </div>
      </header>

      <main className="content-shell">
        <section className="hero-copy">
          <h2>Inspection Cases</h2>
          <p>
            Review sample German inspection recordings, trigger the extraction workflow,
            review field updates, and approve the final update payload.
          </p>
        </section>

        <section className="case-list">
          {sampleCases.map((item) => (
            <CaseCard item={item} key={item.suspicionId} />
          ))}
        </section>
      </main>
    </div>
  );
}
