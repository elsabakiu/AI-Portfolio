# Observability Alerts

Configure these alerts in Sentry once the three projects are connected:

## API Project

- Extraction failures spike
  - Condition: `workflow_stage:workflow_execution` and error count above normal baseline over 5 minutes
- 5xx response spike
  - Condition: `service:api` and `level:error` with HTTP status `>=500`
- Abnormal latency
  - Condition: p95 transaction duration for extraction endpoints above 3 seconds over 10 minutes
- Send-to-InfraCloud failures
  - Condition: `stage:send_to_infracloud` error count above threshold

## Web Project

- Render error regression
  - Condition: new issue in `service:web` on production or staging
- API interaction failures
  - Condition: `api_path:/extract` or `api_path:/send-to-infracloud` with elevated error rate

## Workflow Project

- Repeated low-confidence audio events
  - Condition: warning or breadcrumb volume associated with `audio_quality_flag:low_confidence`
- Upstream model failures
  - Condition: `stage:transcribe_audio` or `stage:extract_fields` exception count above threshold
- Workflow node failure spike
  - Condition: node-level exceptions grouped by `stage`
