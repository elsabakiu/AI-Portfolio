interface TranscriptPanelProps {
  transcript?: string;
}

export function TranscriptPanel({ transcript }: TranscriptPanelProps) {
  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>Transcript</h2>
          <p>Final transcript returned by the extraction workflow.</p>
        </div>
      </div>
      <blockquote className="transcript">“{transcript || "No transcript returned."}”</blockquote>
    </section>
  );
}
