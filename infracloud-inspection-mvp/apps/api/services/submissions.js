import crypto from "node:crypto";
import { logger } from "../lib/logger.js";

export function createSubmissionsService(db, inspectionCasesService, auditService, metrics) {
  async function createSubmission({ suspicionId, proposal, actor, requestId }) {
    try {
      return await db.withTransaction(async (client) => {
        const id = crypto.randomUUID();
        const sentAt = new Date().toISOString();
        const mode = "mock-send";

        await inspectionCasesService.upsertCase(
          {
            suspicionId,
            latestProposal: proposal,
          },
          client
        );

        await client.query(
          `
          INSERT INTO submissions (
            id,
            suspicion_id,
            proposal,
            actor_id,
            actor_role,
            request_id,
            mode,
            sent_at
          )
          VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8)
        `,
          [
            id,
            suspicionId,
            JSON.stringify(proposal),
            actor.userId,
            actor.role,
            requestId,
            mode,
            sentAt,
          ]
        );

        await auditService.recordEvent(
          {
            suspicionId,
            actorId: actor.userId,
            actorRole: actor.role,
            requestId,
            action: "submission.created",
            entityType: "submission",
            entityId: id,
            eventData: {
              mode,
            },
          },
          client
        );

        return {
          id,
          sentAt,
          mode,
        };
      });
    } catch (error) {
      metrics.increment("workflow_send_failures", {});
      logger.error("Sending submission failed", {
        suspicion_id: suspicionId,
        request_id: requestId,
        stage: "send_to_infracloud",
        actor_id: actor.userId,
        error: error instanceof Error ? error : new Error(String(error)),
      });
      throw error;
    }
  }

  return {
    createSubmission,
  };
}
