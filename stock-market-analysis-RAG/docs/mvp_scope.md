# MVP Scope

## In scope

- Index local filings/transcripts
- Run retrieval + grounded answer generation
- Provide observability metrics and logs
- CLI outputs in console/JSON format

## Out of scope (v0.1.0)

- Real-time market/news ingestion
- Portfolio optimization recommendations
- Multi-user web app
- Persistent long-term run history

## Success criteria

- Pipeline runs end-to-end on dataset without manual code changes
- Failure in one doc does not stop whole run
- Users can inspect retrieved evidence per answer
