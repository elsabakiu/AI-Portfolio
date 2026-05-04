export type ReviewRecord = Record<string, unknown>;

export interface ExistingRecord extends ReviewRecord {}
export interface Proposal extends ReviewRecord {}

export interface SampleCase {
  suspicionId: number;
  title: string;
  summary: string;
  status: "ready" | "attention";
  reviewState: string;
  updateCount: number;
  riskLevel: string;
  audioUrl: string;
  recordUrl: string;
  scenario: string;
}

export interface Conflict {
  field: string;
  existing_value: unknown;
  extracted_value: unknown;
  proposed_resolution: string;
}

export interface WorkflowWarning {
  type: string;
  stage: string;
  message: string;
  node?: string;
  word_count?: number;
  [key: string]: unknown;
}

export interface WorkflowDiagnostics {
  stages: Record<string, string>;
  start_time: string | null;
}

export interface ExtractionResult {
  run_id?: string;
  workflow_run_id?: string;
  suspicion_id: string;
  audio_quality_flag?: string;
  rerecord_suggestion?: string | null;
  word_count?: number;
  transcript?: string;
  intent?: string | null;
  extracted_fields?: ReviewRecord;
  confidence?: Record<string, number | string>;
  catalog_validation?: Record<string, unknown>;
  partial_catalog?: boolean;
  conflicts?: Conflict[];
  langsmith_run_id?: string;
  warnings?: WorkflowWarning[];
  diagnostics?: WorkflowDiagnostics;
  simulated_infracloud_payload?: Proposal;
}

export interface WorkflowRunRecord {
  workflow_run_id: string;
  suspicion_id: string;
  status: string;
  provider: string;
  upstream_run_id?: string | null;
  started_at: string;
  finished_at: string;
  actor_id?: string | null;
  actor_role?: string | null;
  request_id?: string | null;
  response: ExtractionResult;
}

export interface DraftPayload {
  suspicion_id: number | string;
  proposal: Proposal;
  savedAt?: string;
  transcript?: string | null;
  workflow_run_id?: string | null;
}

export interface Submission {
  suspicion_id: number | string;
  proposal: Proposal;
  sentAt?: string;
  mode?: string;
}

export interface SaveDraftResult {
  savedAt: string;
}

export interface SendResult {
  sentAt: string;
  mode: string;
}

export interface ApiMeta {
  requestId: string;
}

export interface ApiSuccess<T> {
  ok: true;
  data: T;
  meta: ApiMeta;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  requestId?: string;
  details?: unknown;
}

export interface ApiFailure {
  ok: false;
  error: ApiErrorPayload;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiFailure;
