import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { WorkflowWarning } from "@schemas/domain";
import { titleFromKey } from "@config/format";

interface DiagnosticsPanelProps {
  diagnostics?: Record<string, string>;
  warnings?: WorkflowWarning[];
}

export function DiagnosticsPanel({ diagnostics = {}, warnings = [] }: DiagnosticsPanelProps) {
  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>Diagnostics</h2>
          <p>Workflow health signals and reviewer-facing warnings.</p>
        </div>
      </div>
      <div className="diagnostics-grid">
        {Object.entries(diagnostics).map(([key, value]) => (
          <div className="diagnostic-pill" key={key}>
            {value === "ok" ? (
              <CheckCircle2 size={16} className="diagnostic-pill__ok" />
            ) : (
              <AlertTriangle size={16} className="diagnostic-pill__warn" />
            )}
            <span>{titleFromKey(key)}</span>
          </div>
        ))}
      </div>
      {warnings.length > 0 && (
        <div className="warning-list">
          {warnings.map((warning, index) => (
            <div className="warning-item" key={`${warning.stage}-${index}`}>
              <AlertTriangle size={16} />
              <span>{warning.message}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
