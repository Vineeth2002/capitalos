
---

## Implementation Status (Phase 12.1)

Code implementation of the approved design is complete locally:
Security, Listing, IngestionRun, SourceRecord models and APIs; FinancialFact
subject rule (entity/security/listing with DB CHECK); published_at and
recorded_at; supersedes_id corrections; ingestion provenance.

NOT done: the production migration. The deployed financial_facts table
still has the old schema and must be dropped and recreated after the
pre-flight checks. Until that happens this document must not be read as
claiming the production migration is complete.

Deviations from the design text: SecurityCreate requires identifier_type
and identifier together or neither; ingestion is atomic per run;
source_record_identifier is only honored inside ingest_from_provider().