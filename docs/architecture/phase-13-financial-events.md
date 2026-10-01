\# CapitalOS — Phase 13: Financial Events



\## What this closes

Section 4 of the Phase 12.1 audit named Event as a real gap: a discrete

occurrence (leadership change, dividend declaration, trading halt) had no

home. It did not fit FinancialFact (a numeric observation) or Claim

(a piece of reasoning about something).



\## Design

Event reuses, unchanged, every foundation Phase 12.1 established:

\- Subject rule: exactly one of entity\_id / security\_id / listing\_id,

&#x20; enforced by the same CHECK-constraint pattern as FinancialFact.

\- Provenance: source\_id (human citation) and source\_record\_id

&#x20; (ingestion lineage), identical to FinancialFact.

\- Correction: supersedes\_id points backward from a new row to the one it

&#x20; corrects; old rows are never mutated. Same as FinancialFact.

\- Time: published\_at (public availability) and recorded\_at (system

&#x20; write time, NOT a look-ahead gate) are reused unchanged.



\## What's different from FinancialFact

An event has one domain-time field, event\_date, not a period pair plus

an as\_of\_date. An event is a single occurrence, not a flow or a stock

measure, so it does not need the flow/point distinction FinancialFact

carries. event\_date is nullable: an event's exact date is sometimes

genuinely unknown or approximate when first recorded, and a later

correction (supersedes\_id) is how a firmer date replaces an earlier one.



description is a required free-text field. event\_type is a free string,

same deliberate choice as FinancialFact.fact\_type - a fixed vocabulary is

future work, not a precondition for this table existing.



\## Known boundary risk: event\_type / description as an unconstrained catch-all

event\_type is a free string and description is unconstrained free text.

Nothing in the model, schema, or service layer stops someone from creating

an Event whose description actually holds a numeric observation that

belongs in FinancialFact instead ("Q1 revenue was 10 crore" as an Event

description, rather than a FinancialFact row). This is not a new risk

introduced by Event - FinancialFact.fact\_type has the identical exposure,

accepted and left unaddressed since Phase 11B/12 - but it is worth naming

explicitly now that a second free-string-typed table exists, since the

exposure compounds: a future reader deciding "is this a Fact or an Event"

has no schema-level guidance either way.



No validation is added in this phase. The fix, when it is built, is almost

certainly a shared classification/vocabulary layer (a registered set of

fact\_types and event\_types, with a rule for which table a given type

belongs to), not a fix to either table in isolation - that layer is

explicitly listed as future work below, not a precondition for this phase

closing.



\## Explicitly not built in this phase

\- No Event-to-FinancialFact or Event-to-Claim relationship table.

\- No event\_type vocabulary or validation against a fixed list, and no

&#x20; shared Fact/Event classification layer (see risk note above).

\- No duration support: event\_date is a single point in time; an event

&#x20; with a start and end (e.g. a trading halt from 10:00 to 10:45) cannot

&#x20; be represented without approximating to one date.

\- No observed/derived/inferred distinction - every Event, like every

&#x20; FinancialFact, is implicitly "observed," with no field marking a

&#x20; computed or AI-inferred value as different in kind.

\- No Challenger integration - the reasoning layer does not read Events yet.

\- No frontend surface for Events.



\## Migration

Purely additive: one new table, no existing table altered. No destructive

step is required. Base.metadata.create\_all() creates it automatically

on the next deploy.

