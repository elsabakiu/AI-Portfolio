import crypto from "node:crypto";
import { AppError } from "../lib/errors.js";
import { logger } from "../lib/logger.js";
import { addBreadcrumb, captureServerException } from "../lib/sentry.js";
import { runWorkflow } from "./workflowClients.js";

export function createExtractionService(
  db,
  config,
  inspectionCasesService,
  auditService,
  metrics
) {
  async function runExtraction({ suspicionId, existingRecord, file, requestId, actor }) {
    const startedAt = new Date().toISOString();
    const workflowRunId = crypto.randomUUID();
    const startedAtMs = Date.now();
    metrics.increment("workflow_extractions_requested", {
      provider: "langgraph",
    });

    await inspectionCasesService.upsertCase({
      suspicionId,
      existingRecord,
    });

    await auditService.recordEvent({
      suspicionId,
      actorId: actor.userId,
      actorRole: actor.role,
      requestId,
      action: "extraction.requested",
      entityType: "workflow_run",
      entityId: workflowRunId,
      eventData: {},
    });

    try {
      addBreadcrumb({
        category: "workflow",
        message: "Starting extraction request",
        level: "info",
        data: {
          suspicion_id: String(suspicionId),
          workflow_run_id: workflowRunId,
        },
      });

      const { response, payload, provider } = await runWorkflow({
        config,
        file,
        suspicionId,
        existingRecord,
      });
      const finishedAt = new Date().toISOString();

      await db.query(
        `
          INSERT INTO workflow_runs (
            id,
            suspicion_id,
            actor_id,
            actor_role,
            request_id,
            status,
            upstream_run_id,
            provider,
            intent,
            transcript,
            warnings,
            diagnostics,
            response_json,
            started_at,
            finished_at
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12::jsonb, $13::jsonb, $14, $15)
        `,
        [
          workflowRunId,
          suspicionId,
          actor.userId,
          actor.role,
          requestId,
          response.ok ? "succeeded" : "failed",
          payload.langsmith_run_id || null,
          provider,
          payload.intent || null,
          payload.transcript || null,
          JSON.stringify(payload.warnings || []),
          JSON.stringify(payload.diagnostics || {}),
          JSON.stringify(payload),
          startedAt,
          finishedAt,
        ]
      );

      await inspectionCasesService.upsertCase({
        suspicionId,
        existingRecord,
        latestProposal: payload.simulated_infracloud_payload || null,
        lastWorkflowRunId: workflowRunId,
      });

      if (!response.ok) {
        throw new AppError(
          response.status,
          "EXTRACTION_UPSTREAM_ERROR",
          payload.message || "Extraction workflow returned an error.",
          payload
        );
      }

      await auditService.recordEvent({
        suspicionId,
        actorId: actor.userId,
        actorRole: actor.role,
        requestId,
        action: "extraction.completed",
        entityType: "workflow_run",
        entityId: workflowRunId,
        eventData: {
          status: "succeeded",
          upstreamRunId: payload.langsmith_run_id || null,
          provider,
        },
      });

      const durationMs = Date.now() - startedAtMs;
      metrics.observe("workflow_extraction_latency_ms", durationMs, {
        provider,
        status: "succeeded",
      });
      metrics.increment("workflow_extractions_completed", {
        provider,
        status: "succeeded",
      });

      if (payload.audio_quality_flag === "low_confidence") {
        metrics.increment("workflow_low_confidence_transcripts", {
          provider,
        });
      }

      logger.info("Extraction workflow completed", {
        suspicion_id: suspicionId,
        workflow_run_id: workflowRunId,
        request_id: requestId,
        provider,
        duration_ms: durationMs,
        stage: "workflow_execution",
      });

      return {
        ...payload,
        workflow_run_id: workflowRunId,
      };
    } catch (error) {
      const finishedAt = new Date().toISOString();
      const details =
        error instanceof AppError
          ? { code: error.code, details: error.details }
          : { message: error instanceof Error ? error.message : String(error) };
      const durationMs = Date.now() - startedAtMs;

      await db.query(
        `
          INSERT INTO workflow_runs (
            id,
            suspicion_id,
            actor_id,
            actor_role,
            request_id,
            status,
            upstream_run_id,
            provider,
            intent,
            transcript,
            warnings,
            diagnostics,
            response_json,
            started_at,
            finished_at
          )
          VALUES ($1, $2, $3, $4, $5, 'failed', NULL, 'unknown', NULL, NULL, '[]'::jsonb, '{}'::jsonb, $6::jsonb, $7, $8)
          ON CONFLICT (id) DO NOTHING
        `,
        [
          workflowRunId,
          suspicionId,
          actor.userId,
          actor.role,
          requestId,
          JSON.stringify(details),
          startedAt,
          finishedAt,
        ]
      );

      await auditService.recordEvent({
        suspicionId,
        actorId: actor.userId,
        actorRole: actor.role,
        requestId,
        action: "extraction.failed",
        entityType: "workflow_run",
        entityId: workflowRunId,
        eventData: details,
      });

      metrics.observe("workflow_extraction_latency_ms", durationMs, {
        provider: "langgraph",
        status: "failed",
      });
      metrics.increment("workflow_extractions_completed", {
        provider: "langgraph",
        status: "failed",
      });

      if (
        error instanceof AppError &&
        ["UPSTREAM_UNAVAILABLE", "EXTRACTION_UPSTREAM_ERROR"].includes(error.code)
      ) {
        metrics.increment("workflow_upstream_model_errors", {
          provider: "langgraph",
        });
      }

      captureServerException(error instanceof Error ? error : new Error(String(error)), {
        service: "api",
        stage: "workflow_execution",
        suspicion_id: suspicionId,
        workflow_run_id: workflowRunId,
      });

      logger.error("Extraction workflow failed", {
        suspicion_id: suspicionId,
        workflow_run_id: workflowRunId,
        request_id: requestId,
        stage: "workflow_execution",
        duration_ms: durationMs,
        details,
        error: error instanceof Error ? error : new Error(String(error)),
      });

      throw error;
    }
  }

  async function getWorkflowRun(runId) {
    const { rows } = await db.query(
      `
        SELECT
          id,
          suspicion_id,
          actor_id,
          actor_role,
          request_id,
          status,
          upstream_run_id,
          provider,
          intent,
          transcript,
          warnings,
          diagnostics,
          response_json,
          started_at,
          finished_at
        FROM workflow_runs
        WHERE id = $1 OR upstream_run_id = $1
        ORDER BY finished_at DESC
        LIMIT 1
      `,
      [runId]
    );

    if (rows.length === 0) {
      return null;
    }

    const row = rows[0];
    const responseJson = row.response_json || {};

    return {
      workflow_run_id: row.id,
      suspicion_id: String(row.suspicion_id),
      status: row.status,
      provider: row.provider,
      upstream_run_id: row.upstream_run_id,
      started_at: row.started_at,
      finished_at: row.finished_at,
      actor_id: row.actor_id,
      actor_role: row.actor_role,
      request_id: row.request_id,
      response: {
        ...responseJson,
        workflow_run_id: row.id,
      },
    };
  }

  return {
    runExtraction,
    getWorkflowRun,
  };
}
