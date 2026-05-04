import crypto from "node:crypto";

export function createAuditService(db) {
  async function recordEvent(event, client = db) {
    const id = crypto.randomUUID();

    await client.query(
      `
        INSERT INTO audit_events (
          id,
          suspicion_id,
          actor_id,
          actor_role,
          request_id,
          action,
          entity_type,
          entity_id,
          event_data
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
      `,
      [
        id,
        event.suspicionId ?? null,
        event.actorId ?? null,
        event.actorRole ?? null,
        event.requestId ?? null,
        event.action,
        event.entityType,
        event.entityId ?? null,
        JSON.stringify(event.eventData || {}),
      ]
    );

    return id;
  }

  return {
    recordEvent,
  };
}
