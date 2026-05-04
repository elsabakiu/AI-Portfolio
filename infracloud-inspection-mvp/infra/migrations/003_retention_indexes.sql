CREATE INDEX IF NOT EXISTS workflow_runs_finished_at_idx
  ON workflow_runs (finished_at);

CREATE INDEX IF NOT EXISTS drafts_saved_at_idx
  ON drafts (saved_at);

CREATE INDEX IF NOT EXISTS submissions_sent_at_idx
  ON submissions (sent_at);

CREATE INDEX IF NOT EXISTS audit_events_created_at_idx
  ON audit_events (created_at);
