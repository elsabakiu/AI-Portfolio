import crypto from "node:crypto";
import { diffRecords } from "../lib/diff.js";
import { logger } from "../lib/logger.js";

export function createDraftsService(db, inspectionCasesService, auditService, metrics) {
  async function getLatestDraftBySuspicionId(suspicionId) {
    const { rows } = await db.query(
      `
        SELECT
          d.id,
          d.suspicion_id,
          d.proposal,
          d.version,
          d.saved_at,
          wr.id AS workflow_run_id,
          wr.transcript
        FROM drafts d
        LEFT JOIN inspection_cases ic
          ON ic.suspicion_id = d.suspicion_id
        LEFT JOIN workflow_runs wr
          ON wr.id = ic.last_workflow_run_id
        WHERE d.suspicion_id = $1 AND d.is_latest = TRUE
        LIMIT 1
      `,
      [suspicionId]
    );

    if (rows.length === 0) {
      return null;
    }

    return {
      id: rows[0].id,
      suspicion_id: Number(rows[0].suspicion_id),
      proposal: rows[0].proposal,
      version: rows[0].version,
      savedAt: rows[0].saved_at,
      workflow_run_id: rows[0].workflow_run_id || null,
      transcript: rows[0].transcript || null,
    };
  }

  async function saveDraft({ suspicionId, proposal, actor, requestId }) {
    try {
      return await db.withTransaction(async (client) => {
        const { rows } = await client.query(
          `
            SELECT id, proposal, version
            FROM drafts
            WHERE suspicion_id = $1 AND is_latest = TRUE
            LIMIT 1
          `,
          [suspicionId]
        );

        const previousDraft = rows[0] || null;
        const version = previousDraft ? previousDraft.version + 1 : 1;
        const proposalDiff = diffRecords(previousDraft?.proposal || {}, proposal);
        const id = crypto.randomUUID();
        const savedAt = new Date().toISOString();

        await inspectionCasesService.upsertCase(
          {
            suspicionId,
            latestProposal: proposal,
          },
          client
        );

        if (previousDraft) {
          await client.query(
            `UPDATE drafts SET is_latest = FALSE WHERE id = $1`,
            [previousDraft.id]
          );
        }

        await client.query(
          `
            INSERT INTO drafts (
              id,
              suspicion_id,
              proposal,
              proposal_diff,
              actor_id,
              actor_role,
              request_id,
              version,
              is_latest,
              saved_at
            )
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7, $8, TRUE, $9)
          `,
          [
            id,
            suspicionId,
            JSON.stringify(proposal),
            JSON.stringify(proposalDiff),
            actor.userId,
            actor.role,
            requestId,
            version,
            savedAt,
          ]
        );

        await auditService.recordEvent(
          {
            suspicionId,
            actorId: actor.userId,
            actorRole: actor.role,
            requestId,
            action: "draft.saved",
            entityType: "draft",
            entityId: id,
            eventData: {
              version,
              proposalDiff,
            },
          },
          client
        );

        return {
          id,
          savedAt,
          version,
        };
      });
    } catch (error) {
      metrics.increment("workflow_save_draft_failures", {});
      logger.error("Saving draft failed", {
        suspicion_id: suspicionId,
        request_id: requestId,
        stage: "save_draft",
        actor_id: actor.userId,
        error: error instanceof Error ? error : new Error(String(error)),
      });
      throw error;
    }
  }

  return {
    getLatestDraftBySuspicionId,
    saveDraft,
  };
}
