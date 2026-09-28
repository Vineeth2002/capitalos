# CapitalOS Data Boundary

External Provider
    -> Connector.fetch()      provider-native raw records
    -> Connector.normalize()  CanonicalFinancialFact objects
    -> Ingestion service      validates and persists
    -> FinancialFact          canonical structured observation

## Identity: Entity vs Security vs Listing
- Entity is the general identity root. A company is an Entity with
  entity_type "company". There is no Company table.
- Security is an instrument issued by a company Entity
  (issuer_entity_id). It carries one optional canonical identifier.
- Listing is a venue-level listing of a Security (exchange + symbol).
  One security may have many listings (for example NSE and BSE).
- Entity.ticker and Entity.exchange are DEPRECATED convenience fields.
  Financial-world code must never treat them as authoritative.

## FinancialFact subject rule
A fact is about exactly ONE of entity_id, security_id, listing_id. This is
enforced by a database CHECK and by validation. Company-level facts
(revenue) go on the entity; security-level facts on the security;
venue-level observations (price, volume) on the listing.

## Time semantics (timestamps are naive UTC)
- period_start / period_end: the reporting or measurement period.
- as_of_date: the date of a point-in-time observation.
- published_at: when the information became publicly available.
- recorded_at: when CapitalOS wrote the row.
Look-ahead-safe research gates on published_at (a fact with a null
published_at has unknown availability and must be excluded by default).
"What did CapitalOS itself have on date T" gates on recorded_at.
recorded_at is NOT a look-ahead gate: backfilled data is recorded late.

## Append-only rule and corrections
FinancialFact rows are never updated. A correction is a NEW row whose
supersedes_id points back to the row it corrects, with an optional
supersession_reason. The corrected row must share subject and fact_type,
and can be superseded only once. The current value of a series is the row
that no other row supersedes.

## Provenance: three different things
- ResearchSource (source_id): the human-facing citation.
- IngestionRun: one execution of an ingestion call for one provider
  (provider_name, connector_version, status, timing).
- SourceRecord (source_record_id): the originating record within a run, by
  the provider's own identifier. raw_content_reference is a pointer, never
  a payload. A SourceRecord is only created when
  source_record_identifier is present and ingestion goes through
  ingest_from_provider().

## Rules
- Provider-specific identifiers (NSE symbol, ISIN, BSE code, vendor ids)
  never appear in CanonicalFinancialFact. Connectors receive or require
  already-resolved CapitalOS ids; entity resolution is a future capability.
- Ingestion through a provider is atomic: on failure no partial facts are
  kept and the run is marked "failed".
- Adding a provider means adding one connector class and registering it.