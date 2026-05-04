CREATE TABLE IF NOT EXISTS inspection_cases (
  suspicion_id BIGINT PRIMARY KEY,
  existing_record JSONB,
  latest_proposal JSONB,
  last_workflow_run_id TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drafts (
  id TEXT PRIMARY KEY,
  suspicion_id BIGINT NOT NULL REFERENCES inspection_cases(suspicion_id) ON DELETE CASCADE,
  proposal JSONB NOT NULL,
  proposal_diff JSONB NOT NULL DEFAULT '[]'::jsonb,
  actor_id TEXT,
  actor_role TEXT,
  request_id TEXT,
  version INTEGER NOT NULL,
  is_latest BOOLEAN NOT NULL DEFAULT TRUE,
  saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS drafts_latest_unique_idx
  ON drafts (suspicion_id)
  WHERE is_latest = TRUE;

CREATE TABLE IF NOT EXISTS submissions (
  id TEXT PRIMARY KEY,
  suspicion_id BIGINT NOT NULL REFERENCES inspection_cases(suspicion_id) ON DELETE CASCADE,
  proposal JSONB NOT NULL,
  actor_id TEXT,
  actor_role TEXT,
  request_id TEXT,
  mode TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_runs (
  id TEXT PRIMARY KEY,
  suspicion_id BIGINT NOT NULL REFERENCES inspection_cases(suspicion_id) ON DELETE CASCADE,
  actor_id TEXT,
  actor_role TEXT,
  request_id TEXT,
  status TEXT NOT NULL,
  upstream_run_id TEXT,
  provider TEXT NOT NULL DEFAULT 'langgraph',
  intent TEXT,
  transcript TEXT,
  warnings JSONB,
  diagnostics JSONB,
  response_json JSONB NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  suspicion_id BIGINT REFERENCES inspection_cases(suspicion_id) ON DELETE CASCADE,
  actor_id TEXT,
  actor_role TEXT,
  request_id TEXT,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT,
  event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
