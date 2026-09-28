# CapitalOS — Phase 12.1 Focused Architecture Audit (Revision 3)

## 0. Basis and evidence limits

Derived from the models, schemas, services and routes built in Phases 1-12
as shown during development. It is NOT a fresh filesystem scan. Claims that
depend on unseen repository state are marked **[UNVERIFIED]** and are turned
into pre-flight checks in Section 6. This revision supersedes earlier drafts
(see Section 7 for what changed and why).

Guiding principle for every decision below: **prefer deferring things whose
later correction is lossless and mechanical; fix now the things whose later
correction would require reclassifying accumulated data by guesswork.**

---

## 1. Current architecture (condensed)

Layering: `models / schemas / services / api`, plus `app/data/`
(connectors, contracts, ingestion), `core/`, `db/`, Jinja2 + vanilla JS UI.

Tables: `entities`, `research_cases`, `claims`, `claim_relationships`,
`challenge_outputs`, `challenge_output_claims`, `research_sources`,
`claim_sources`, `research_sessions`, `research_events`, `financial_facts`.

Relevant current shapes:
- `Entity`: entity_type (company/person/sector/country/asset/other),
  canonical_name, ticker (nullable), exchange (nullable), status, timestamps.
  Referenced by `ResearchCase.entity_id` and `Claim.entity_id`.
- `FinancialFact`: entity_id (required FK), fact_type (free string),
  value_numeric Numeric(20,6), unit, currency, period_start, period_end,
  as_of_date, source_id (nullable FK to research_sources), created_at.
- Phase 12: `CanonicalFinancialFact` dataclass, `FinancialDataConnector`
  ABC, in-memory registry, `ingest_from_provider()`.

Strengths: uniform layering; LLM-provider isolation proven under real
failures; link tables instead of JSON blobs.
Weaknesses relevant here: Entity conflates identity with a single
ticker/exchange; no update history; `fact_type` is a free string;
FinancialFact has no consumer yet; connector provenance is discarded after
ingestion.

---

## 2. Resolutions of the four open questions

### 2.1 Entity vs Company

| Option | Verdict |
|---|---|
| A. Entity stays general; Company is a specialised concept | Chosen, in its minimal form (no Company table yet) |
| B. Repurpose Entity as Company, move other types out | Rejected: breaks Claim/ResearchCase references to sector/country/person Entities, and those remain valid fact subjects |
| C. Company subtype table (shared PK with entities) | Deferred, additive |

Decision: **Entity remains the general identity root.** A company is an
Entity with `entity_type='company'`. An issuer is the Entity referenced by
`Security.issuer_entity_id` (validated at service layer to be a company).
No Company or Issuer table now.

Why deferral is safe: `entity_type` already discriminates companies, so a
future `companies` subtype table (PK = entity id) can be backfilled by
`SELECT id FROM entities WHERE entity_type='company'` with no ambiguity and
no fact reclassification. The trigger for creating it is the first
company-specific attribute (LEI/CIN, incorporation date, listing status).

`Entity.ticker` and `Entity.exchange` are retained for backward
compatibility and documented as a **deprecated convenience snapshot**.
Financial-world code must never read them as authoritative; `Security` and
`Listing` are authoritative.

### 2.2 Security vs Listing

Decision: **B. Establish a minimal Security + Listing boundary now.**

Reasoning grounded in the target market: an ISIN identifies the security;
the NSE symbol and BSE scrip code identify listings of that same security.
Modelling `exchange` on Security makes multi-listing (normal in India, not
an edge case) create duplicate Security rows. Merging duplicates later means
re-pointing every fact by hand, which is the reclassification problem this
phase exists to avoid. Exchange-specific observations such as a closing
price also have no correct home without Listing, and encoding the venue in
`fact_type` strings ("close_price_nse") is a known anti-pattern.

Minimum now: `securities` (issuer, one canonical identifier) and `listings`
(security, exchange code, symbol). Exchange stays a normalised string
(upper-case at service layer) rather than an `exchanges` table; that is
recoverable later by promoting distinct values to a table.

Deferred: multiple identifiers per security (`security_identifiers`),
identifier validity periods, ticker-change history, security type/asset-class
taxonomy, exchange reference table.

### 2.3 FinancialFact subject

| Option | Verdict |
|---|---|
| A. entity_id + security_id (+ listing_id), real FKs, CHECK exactly one | Chosen (v1 boundary: Entity / Security / Listing) |
| B. FactSubject table with real FKs | Deferred, with an explicit trigger |
| C. Polymorphic subject_type + subject_id | Rejected: no FK enforcement |

Decision: **deliberately limit FinancialFact v1 to three real-FK subject
kinds and accept that the boundary will expand.**

- `entity_id` is kept unchanged. Company facts (revenue, employees) and
  non-company Entity facts (country or sector series) fit it.
- `security_id` holds security-level facts (shares outstanding, and later
  corporate-action-linked facts).
- `listing_id` holds venue-level observations (price, volume).
- CHECK: exactly one of the three is non-null (portable CASE expression,
  not boolean arithmetic, so it works on SQLite and Postgres).

Why not FactSubject now: expanding later (new subject type) means adding one
nullable column and rewriting one CHECK. Moving to FactSubject later means
creating subject rows and re-pointing facts, which is mechanical and
lossless because every fact has exactly one populated FK. Nothing is
reclassified by guesswork. The cost of deferral is code churn, not data
ambiguity.

**Explicit triggers to move to FactSubject:** (1) a fourth subject kind is
needed (index, currency, macro series, fund), or (2) a second table (Event,
Fact-Claim relationship) needs the same "about a subject" reference, since
the N-nullable-FK pattern would otherwise be copied into every such table.
Three FKs is the ceiling of the current pattern.

Known limits accepted for v1: `fact_type` is still a free string, so the
schema cannot enforce fact_type/subject compatibility (e.g. "revenue must
not sit on a listing"). Service-layer validation only checks that exactly
one existing subject is given. A fact_type vocabulary is Phase 13 work.

### 2.4 Time and availability

Six distinct concepts, mapped:

| Concept | Meaning | Home |
|---|---|---|
| Domain/effective time | when the value was true | `as_of_date` (existing) |
| Reporting period | span a flow measure covers | `period_start` / `period_end` (existing) |
| Publication time | when the world could first know it | `published_at` (NEW, nullable) |
| Recorded/ingested time | when CapitalOS wrote the row | `recorded_at` (`created_at` renamed on this table) |
| Availability for reasoning | derived, not stored: publication-time gate for research, recorded-time gate for postmortems | query rule |
| Revision/restatement time | when a correction entered | the correcting row's `recorded_at` |

Correction to my earlier draft: `created_at` is **not** availability time.
Two different point-in-time questions exist and they use different columns:
- **Research/backtest ("what could a market participant know on date T?")**
  uses `published_at <= T`. Backfilled data recorded in 2026 for a 2024
  filing has `recorded_at` in 2026 but a 2024 `published_at`; recorded time
  would wrongly hide it.
- **Decision postmortem ("what did CapitalOS itself have on date T?")**
  uses `recorded_at <= T`.

Look-ahead rule: a fact with `published_at IS NULL` has unknown availability
and must be excluded from look-ahead-safe research by default. That rule is
the trap-avoidance mechanism, and it is why `published_at` is worth its
one column now.

Naming: no column is called `available_at`; the word conflates the two
questions above. Use `published_at` (world) and `recorded_at` (system).
Renaming `created_at` to `recorded_at` is done on `financial_facts` only,
because that table is being recreated anyway. Other tables keep
`created_at`; this inconsistency is accepted deliberately.

Corrections: `supersedes_id` on the NEW row points back to the row it
corrects. Old rows are never written after insertion. A UNIQUE constraint on
`supersedes_id` prevents branching; a CHECK forbids self-supersession.
Service layer requires the corrected row to share subject and fact_type.
"Current value" = a row that no other row supersedes. `supersession_reason`
is a plain nullable string. No revision-time column is needed.

Deferred: a stored `available_at`, a temporal query API, multi-level
branching supersession, bitemporal validity intervals.

---

## 3. Provenance (unchanged from Revision 2 except one added column)

Minimum required now, answering: who supplied it / which feed / which run /
which source record / when ingested / which normalization version.

- `ingestion_runs`: id, provider_name, connector_version (nullable),
  status, started_at, completed_at (nullable), created_at.
- `source_records`: id, ingestion_run_id (FK), record_identifier (the
  provider's own id for the originating record), raw_content_reference
  (nullable pointer, not a payload), created_at,
  UNIQUE(ingestion_run_id, record_identifier).
- `financial_facts.source_record_id` (nullable FK).

`ResearchSource` / `source_id` remain the human-facing citation link and are
not replaced. A "Dataset/Feed" layer above IngestionRun is deferred: no
evidence yet of several feeds per provider, and `provider_name` answers
"which feed" for now. `connector_version` answers "which normalization
version" at run granularity.

Contract consequence: `CanonicalFinancialFact` needs a provider-independent
`source_record_identifier` (string, optional) so the ingestion service can
create one SourceRecord per originating record without knowing provider
field names.

---

## 4. Data-model boundaries (unchanged findings)

Real gaps: Event (no home today), Derived metric (indistinguishable from an
observed fact), Fact-Claim and Fact-Fact relationships. Not gaps:
Hypothesis and Prediction are already expressed by `Claim.epistemic_role`
and `temporal_orientation`; they need no new tables. Decision does not exist
anywhere. None of these gaps block the foundation below.

---

## 5. Phase 12.1 Final Foundation Decision

Design order: **Identity → Security/Listing → Fact subject → Provenance → Time.**

**A. Identity model.** Entity unchanged in structure, remains the general
identity root; company = entity_type 'company'; issuer = role via
`Security.issuer_entity_id`; `Entity.ticker/exchange` deprecated snapshot.

**B. Security/Listing.** `securities` and `listings` as minimal tables.

**C. Fact subject.** `entity_id | security_id | listing_id`, real FKs,
CHECK exactly one.

**D. Provenance.** `ingestion_runs` + `source_records` + `source_record_id`.

**E. Time/correction.** `published_at` added, `created_at` becomes
`recorded_at` on financial_facts, `supersedes_id` (+ UNIQUE, no
self-reference) and `supersession_reason`.

### Exact schema changes now

```
securities
  id PK
  issuer_entity_id FK entities.id NOT NULL, indexed
  identifier_type str NULL
  identifier str NULL
  created_at
  UNIQUE (identifier_type, identifier)

listings
  id PK
  security_id FK securities.id NOT NULL, indexed
  exchange str NOT NULL
  symbol str NOT NULL
  created_at
  UNIQUE (security_id, exchange, symbol)

ingestion_runs
  id PK, provider_name NOT NULL indexed, connector_version NULL,
  status NOT NULL, started_at NOT NULL, completed_at NULL, created_at

source_records
  id PK, ingestion_run_id FK NOT NULL indexed,
  record_identifier NOT NULL, raw_content_reference NULL, created_at
  UNIQUE (ingestion_run_id, record_identifier)

financial_facts (dropped and recreated)
  id PK
  entity_id FK NULL, security_id FK NULL, listing_id FK NULL
  CHECK exactly one of the three is non-null
  fact_type, value_numeric, unit, currency,
  period_start, period_end, as_of_date            (unchanged)
  published_at DateTime NULL                      (new)
  source_id FK research_sources NULL              (unchanged)
  source_record_id FK source_records NULL         (new)
  supersedes_id FK financial_facts NULL, UNIQUE   (new)
  supersession_reason str NULL                    (new)
  recorded_at DateTime server_default now         (was created_at)
  CHECK supersedes_id IS NULL OR supersedes_id <> id
```

### Exact code changes now
- New models: Security, Listing, IngestionRun, SourceRecord. Register in
  `app/main.py`.
- `FinancialFact` model rebuilt as above.
- `FinancialFactCreate/Response`: entity_id becomes optional; add
  security_id, listing_id, published_at, source_record_id, supersedes_id,
  supersession_reason; Pydantic validator enforces exactly one subject;
  response exposes `recorded_at`.
- `financial_fact_service`: validate exactly one subject exists; validate
  supersession rules (same subject, same fact_type, target not already
  superseded).
- New minimal services/routes for creating and reading securities and
  listings (issuer must exist and have entity_type 'company'; exchange
  upper-cased).
- `CanonicalFinancialFact`: add security_id, listing_id, published_at,
  source_record_identifier (use keyword-only fields so existing mock
  connectors keep working).
- `ingest_from_provider()`: create one IngestionRun per call, one
  SourceRecord per distinct source_record_identifier, attach
  source_record_id; mark run completed/failed.
- Tests: update Phase 11B/12 tests where they touch created_at; add tests
  for the CHECK constraint, security/listing creation and rules, run and
  record provenance, supersession rules, published_at persistence.
- `app/data/README.md`: document append-only rule and the two
  point-in-time gates.

### Unchanged
Entity structure, ResearchCase, Claim, ClaimRelationship, Challenger,
ResearchSource, ClaimSource, ResearchSession/ResearchEvent, the connector
ABC and registry concept, all Phase 6-10 behaviour. `POST /financial-facts`
callers that pass `entity_id` keep working.

### Deferred
Company subtype table; multiple identifiers; ticker/identifier history;
corporate actions; security type taxonomy; exchange table; Dataset/Feed
layer; stored `available_at`; temporal query API; FactSubject; fact_type
vocabulary/registry; Event model; Fact-Claim and Fact-Fact relationships;
derived metrics.

### Phase 13 can safely build on
Stable Entity/Security/Listing identity; a fact subject that cannot be
ambiguous; full provenance from fact back to provider run and source record;
immutable facts with explicit corrections; the two point-in-time gates.

### Phase 13 must NOT assume
- That provider identifiers (NSE symbol, ISIN, BSE code) are CapitalOS ids.
  A resolution service must map them, and connectors still need
  already-resolved ids.
- That `Entity.ticker/exchange` are authoritative.
- That `recorded_at` answers look-ahead questions; only `published_at` does.
- That facts can be updated in place, or that `fact_type` strings are
  normalised across providers ("Revenue" and "revenue" are still distinct).
- That FinancialFact can absorb a fourth subject kind without triggering the
  FactSubject migration.

---

## 6. Migration strategy and pre-flight

`Base.metadata.create_all()` creates missing tables only; it never alters an
existing one. So four new tables appear automatically, but the deployed
`financial_facts` table must be dropped and recreated. This is a
destructive step and needs an explicit DB delete decision (YES) at
implementation time, after these checks:

1. **[UNVERIFIED] Production contents.** `GET /financial-facts` on local and
   on production; confirm only smoke-test rows exist.
2. **[UNVERIFIED] Usage scan.** Search the repository for `created_at` on
   financial facts and for `entity_id` in `app/data` and financial routes;
   list every reference the rebuild touches.
3. Take a Postgres dump or export of `financial_facts` before dropping.

Sequence: deploy new code, drop old `financial_facts` (only that table),
restart the service so `create_all()` recreates it, then verify with a
create/read/supersede smoke test. Only `/financial-facts` endpoints are
affected during the window; no other feature reads that table. Local test
databases rebuild themselves each run.

---

## 7. What changed from earlier drafts

| Earlier position | Now | Why |
|---|---|---|
| Repurpose Entity as Company | Entity stays general | Claims and facts legitimately use non-company Entities |
| Security carries `exchange` | Security + Listing | ISIN vs per-venue symbol; NSE/BSE multi-listing is the norm |
| company_id / security_id | entity_id / security_id / listing_id | Less churn; correct home for venue-level facts |
| `created_at` = availability time | `recorded_at` + new `published_at` | Backtests need publication time; postmortems need recorded time |
| `superseded_by_id` (old to new) | `supersedes_id` (new to old) | Old rows never mutated |
| `raw_record_reference` on IngestionRun | `source_records` table | Many records per run; avoid a catch-all field |
| Fact-Claim relationship first in Phase 13 | Identity, time, provenance first | Ordering by dependency, not by implementation ease |

## Decision table

| Decision | Implement now | Defer | Reason |
|---|---|---|---|
| Entity stays general, no Company table | ✅ | Company subtype | Company subtype is losslessly backfillable from entity_type |
| Security + Listing | ✅ | | Multi-listing is normal; merging duplicate securities later means manual fact reclassification |
| entity/security/listing FKs + CHECK | ✅ | FactSubject | Expanding later is mechanical; loses no information |
| Multiple identifiers, identifier history | | ✅ | Additive; nothing depends on it yet |
| IngestionRun + SourceRecord | ✅ | | Provenance not captured at ingestion cannot be reconstructed |
| Dataset/Feed layer | | ✅ | No multi-feed provider yet |
| published_at + recorded_at rename | ✅ | | Prevents the look-ahead trap before real data exists |
| Stored available_at, temporal query API | | ✅ | Derivable from the two columns above |
| supersedes_id + reason | ✅ | Branching supersession | Restatements are certain in real data; immutability must hold from day one |
| fact_type vocabulary | | ✅ | Phase 13; mapping is recoverable |
| Event, Fact-Claim relationships | | ✅ | Depend on stable subject and identity |

## DO NOT IMPLEMENT YET (Phase 13+)
Discovery, decision, portfolio/risk, model governance, multi-tenancy,
learning/validation, real provider connectors, entity-resolution engine,
Challenger consumption of facts, dashboards.

## FINAL IMPLEMENTATION READINESS

**READY FOR IMPLEMENTATION**

This applies to the design. Two conditions attach, and both are the
pre-flight checks in Section 6: the design was derived without direct
repository access, and dropping the deployed `financial_facts` table
depends on confirming it holds only test data. If either check turns up
something unexpected, stop and revisit Sections 2.3 and 6 before writing
code.
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