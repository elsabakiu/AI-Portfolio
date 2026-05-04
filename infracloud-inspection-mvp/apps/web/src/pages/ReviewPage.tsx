import { ArrowLeft, CircleAlert, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Sentry } from "../instrument";
import { ActionBar } from "@ui/components/ActionBar";
import { AudioPlayerCard } from "@ui/components/AudioPlayerCard";
import { ComparisonTable } from "@ui/components/ComparisonTable";
import { TranscriptPanel } from "@ui/components/TranscriptPanel";
import { getDraft, ApiError, extractInspection, saveDraft, sendToInfraCloud } from "../lib/api";
import { getSampleCaseById } from "../data/sampleCases";
import type { ExistingRecord, ExtractionResult, Proposal } from "@schemas/domain";
import { normalizeFieldValue, validateProposal } from "../lib/validation";

const HIDDEN_REVIEW_FIELDS = ["Created at"];

type LoadState = "idle" | "loading" | "ready" | "error";
type ExtractionState = "idle" | "extracting" | "done" | "error";

export function ReviewPage() {
  const { id } = useParams();
  const sample = getSampleCaseById(id);
  const [existingRecord, setExistingRecord] = useState<ExistingRecord | null>(null);
  const [recordState, setRecordState] = useState<LoadState>("idle");
  const [recordError, setRecordError] = useState<string>("");
  const [draftState, setDraftState] = useState<LoadState>("idle");
  const [draftError, setDraftError] = useState<string>("");
  const [workflowResult, setWorkflowResult] = useState<ExtractionResult | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [status, setStatus] = useState<ExtractionState>("idle");
  const [message, setMessage] = useState("");
  const [saveError, setSaveError] = useState("");
  const [sendError, setSendError] = useState("");
  const [draftSaved, setDraftSaved] = useState(false);
  const [approved, setApproved] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const [lastSentAt, setLastSentAt] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showUpdatedOnly, setShowUpdatedOnly] = useState(true);

  useEffect(() => {
    Sentry.setTag("page", "review");
    if (sample) {
      Sentry.setTag("suspicion_id", String(sample.suspicionId));
      Sentry.setContext("review_case", {
        suspicion_id: sample.suspicionId,
        title: sample.title,
      });
    }
  }, [sample]);

  useEffect(() => {
    if (!sample) return;
    const activeSample = sample;

    let active = true;

    async function loadCase() {
      setRecordState("loading");
      setDraftState("loading");
      setRecordError("");
      setDraftError("");
      setWorkflowResult(null);
      setStatus("idle");
      setMessage("");
      setSaveError("");
      setSendError("");
      setApproved(false);
      setSent(false);
      setLastSentAt(null);

      try {
        const recordResponse = await fetch(activeSample.recordUrl);
        if (!recordResponse.ok) {
          throw new Error("Failed to load the existing record.");
        }

        const recordPayload = (await recordResponse.json()) as ExistingRecord;
        if (!active) return;

        setExistingRecord(recordPayload);
        setRecordState("ready");
        setProposal(recordPayload);
        setValidationErrors({});

        try {
          const draftPayload = await getDraft(activeSample.suspicionId);
          if (!active) return;

          const validatedDraft = validateProposal(draftPayload.proposal);
          setProposal(validatedDraft.proposal);
          setValidationErrors(validatedDraft.errors);
          setWorkflowResult(
            draftPayload.transcript || draftPayload.workflow_run_id
              ? {
                  suspicion_id: String(activeSample.suspicionId),
                  workflow_run_id: draftPayload.workflow_run_id || undefined,
                  transcript: draftPayload.transcript || undefined,
                }
              : null
          );
          setLastSavedAt(draftPayload.savedAt || null);
          setDraftSaved(true);
          setDraftState("ready");
        } catch (error) {
          if (!active) return;

          if (error instanceof ApiError && error.status === 404) {
            setDraftSaved(false);
            setDraftState("ready");
            return;
          }

          setDraftState("error");
          setDraftError(error instanceof Error ? error.message : String(error));
        }
      } catch (error) {
        if (!active) return;
        setRecordState("error");
        setRecordError(error instanceof Error ? error.message : String(error));
      }
    }

    void loadCase();

    return () => {
      active = false;
    };
  }, [sample]);

  const changedCount = useMemo(() => {
    if (!existingRecord || !proposal) return 0;
    return Object.keys(proposal).filter(
      (key) =>
        !HIDDEN_REVIEW_FIELDS.includes(key) &&
        JSON.stringify(existingRecord[key]) !== JSON.stringify(proposal[key])
    ).length;
  }, [existingRecord, proposal]);

  const validationCount = Object.keys(validationErrors).length;
  const hasValidationErrors = validationCount > 0;
  const lowConfidenceCount = useMemo(() => {
    return Object.values(workflowResult?.confidence || {}).filter((value) => {
      const score = Number(value);
      return Number.isFinite(score) && score < 0.65;
    }).length;
  }, [workflowResult]);
  const canReview = Boolean(existingRecord && proposal && (workflowResult || draftSaved));

  if (!sample) {
    return (
      <div className="empty-state">
        <p>Case not found.</p>
      </div>
    );
  }

  const currentSample = sample;

  async function runExtraction() {
    if (!existingRecord) return;

    setStatus("extracting");
    setMessage("");
    setSaveError("");
    setSendError("");
    setDraftSaved(false);
    setApproved(false);
    setSent(false);

    try {
      const audioResponse = await fetch(currentSample.audioUrl);
      if (!audioResponse.ok) {
        throw new Error("Failed to load the sample audio.");
      }

      const audioBlob = await audioResponse.blob();
      const formData = new FormData();
      formData.append("audio_file", audioBlob, `${currentSample.suspicionId}.wav`);
      formData.append("suspicion_id", String(currentSample.suspicionId));
      formData.append("existing_record", JSON.stringify(existingRecord));

      const payload = await extractInspection(formData);
      setWorkflowResult(payload);

      const validatedProposal = validateProposal(
        payload.simulated_infracloud_payload || existingRecord
      );
      setProposal(validatedProposal.proposal);
      setValidationErrors(validatedProposal.errors);
      setStatus("done");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : String(error));
    }
  }

  async function saveAndApprove() {
    if (!proposal) return;

    const validatedProposal = validateProposal(proposal);
    setProposal(validatedProposal.proposal);
    setValidationErrors(validatedProposal.errors);
    setSaveError("");

    if (!validatedProposal.isValid) {
      setApproved(false);
      return;
    }

    try {
      const payload = await saveDraft(currentSample.suspicionId, validatedProposal.proposal);
      setDraftSaved(true);
      setApproved(true);
      setLastSavedAt(payload.savedAt);
    } catch (error) {
      setApproved(false);
      setSaveError(error instanceof Error ? error.message : String(error));
    }
  }

  async function submitToInfraCloud() {
    if (!proposal) return;

    const validatedProposal = validateProposal(proposal);
    setProposal(validatedProposal.proposal);
    setValidationErrors(validatedProposal.errors);
    setSendError("");

    if (!validatedProposal.isValid) {
      setApproved(false);
      return;
    }

    setSending(true);

    try {
      const payload = await sendToInfraCloud(currentSample.suspicionId, validatedProposal.proposal);
      setSent(true);
      setLastSentAt(payload.sentAt);
    } catch (error) {
      setSent(false);
      setSendError(error instanceof Error ? error.message : String(error));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="topbar topbar--compact">
        <div className="topbar__brand">
          <Link className="icon-button icon-button--ghost" to="/">
            <ArrowLeft size={16} />
          </Link>
          <div>
            <p className="mono">#{currentSample.suspicionId}</p>
            <h1>{currentSample.title}</h1>
          </div>
        </div>
        {sent && (
          <div className="topbar__stats">
            <span className="status-inline">
              <ShieldCheck size={14} />
              Sent
            </span>
          </div>
        )}
      </header>

      <main className="content-shell content-shell--review">
        <section className="hero-copy hero-copy--compact">
          <h2>{currentSample.summary}</h2>
          <p>
            Trigger the extraction workflow, review the returned updates against the
            current InfraCloud record, then review and approve changes.
          </p>
        </section>

        <section className="review-workspace-row">
          <AudioPlayerCard audioUrl={currentSample.audioUrl} />

          <section className="panel panel--extraction">
            <div className="panel__header">
              <div>
                <h2>Extraction</h2>
                <p>Run the workflow for this case and load the proposed field update.</p>
              </div>
              <button
                className="button"
                disabled={recordState === "loading" || recordState === "error"}
                onClick={runExtraction}
                type="button"
              >
                {recordState === "loading" ? "Loading Case..." : "Run Extraction"}
              </button>
            </div>

            {recordState === "loading" && (
              <div className="callout callout--info">
                <LoaderCircle size={18} className="spin" />
                <div>
                  <strong>Loading case record…</strong>
                  <p>Preparing the existing InfraCloud record and any saved draft.</p>
                </div>
              </div>
            )}

            {recordState === "error" && (
              <div className="callout callout--danger">
                <CircleAlert size={18} />
                <div>
                  <strong>Case failed to load</strong>
                  <p>{recordError}</p>
                </div>
              </div>
            )}

            {draftState === "error" && (
              <div className="callout callout--danger">
                <CircleAlert size={18} />
                <div>
                  <strong>Saved draft could not be loaded</strong>
                  <p>{draftError}</p>
                </div>
              </div>
            )}

            {draftState === "ready" && draftSaved && lastSavedAt && (
              <div className="callout callout--success">
                <ShieldCheck size={18} />
                <div>
                  <strong>Saved draft restored</strong>
                  <p>Review state resumed from the last local draft saved at {lastSavedAt}.</p>
                </div>
              </div>
            )}

            {status === "extracting" && (
              <div className="callout callout--info">
                <LoaderCircle size={18} className="spin" />
                <div>
                  <strong>Extracting fields…</strong>
                  <p>Transcribing audio, extracting structured data, and validating the result.</p>
                </div>
              </div>
            )}

            {status === "error" && (
              <div className="callout callout--danger">
                <CircleAlert size={18} />
                <div>
                  <strong>Extraction failed</strong>
                  <p>{message}</p>
                </div>
              </div>
            )}

            {status === "done" && (
              <div className="callout callout--success">
                <ShieldCheck size={18} />
                <div>
                  <strong>Extraction complete</strong>
                  <p>{changedCount} field updates were identified for this damage record.</p>
                </div>
              </div>
            )}

            {saveError && (
              <div className="callout callout--danger">
                <CircleAlert size={18} />
                <div>
                  <strong>Save failed</strong>
                  <p>{saveError}</p>
                </div>
              </div>
            )}

            {sendError && (
              <div className="callout callout--danger">
                <CircleAlert size={18} />
                <div>
                  <strong>Send failed</strong>
                  <p>{sendError}</p>
                </div>
              </div>
            )}
          </section>
        </section>

        {canReview && (
          <>
            {workflowResult && (
              <TranscriptPanel
                transcript={workflowResult.transcript}
              />
            )}

            <ComparisonTable
              existingRecord={existingRecord || {}}
              proposedRecord={proposal || {}}
              confidenceByField={workflowResult?.confidence || {}}
              hiddenFields={HIDDEN_REVIEW_FIELDS}
              validationErrors={validationErrors}
              showUpdatedOnly={showUpdatedOnly}
              onToggleShowUpdatedOnly={setShowUpdatedOnly}
              onChange={(key, rawValue) => {
                const normalized = normalizeFieldValue(key, rawValue);
                setDraftSaved(false);
                setApproved(false);
                setSent(false);
                setProposal((current) => ({
                  ...(current || {}),
                  [key]: normalized.value,
                }));
                setValidationErrors((current) => {
                  if (!normalized.error && !current[key]) {
                    return current;
                  }

                  const next = { ...current };
                  if (normalized.error) {
                    next[key] = normalized.error;
                  } else {
                    delete next[key];
                  }
                  return next;
                });
              }}
            />
          </>
        )}

        {!canReview && workflowResult && (
          <TranscriptPanel
            transcript={workflowResult.transcript}
          />
        )}
      </main>

      {canReview && (
        <ActionBar
          onSaveAndApprove={saveAndApprove}
          onSend={submitToInfraCloud}
          draftSaved={draftSaved}
          sending={sending}
          sent={sent}
          hasValidationErrors={hasValidationErrors}
          validationCount={validationCount}
        />
      )}
    </div>
  );
}
