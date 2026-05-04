export function createInspectionCasesService(db) {
  async function upsertCase({ suspicionId, existingRecord, latestProposal, lastWorkflowRunId }, client = db) {
    await client.query(
      `
        INSERT INTO inspection_cases (
          suspicion_id,
          existing_record,
          latest_proposal,
          last_workflow_run_id
        )
        VALUES ($1, $2::jsonb, $3::jsonb, $4)
        ON CONFLICT (suspicion_id)
        DO UPDATE SET
          existing_record = COALESCE(EXCLUDED.existing_record, inspection_cases.existing_record),
          latest_proposal = COALESCE(EXCLUDED.latest_proposal, inspection_cases.latest_proposal),
          last_workflow_run_id = COALESCE(EXCLUDED.last_workflow_run_id, inspection_cases.last_workflow_run_id),
          updated_at = NOW()
      `,
      [
        suspicionId,
        existingRecord ? JSON.stringify(existingRecord) : null,
        latestProposal ? JSON.stringify(latestProposal) : null,
        lastWorkflowRunId || null,
      ]
    );
  }

  return {
    upsertCase,
  };
}
