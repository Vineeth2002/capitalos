\# CapitalOS — Phase 14: Classification and Observed/Derived/Inferred



\## What this closes

The Phase 13 review (point 9) named an inherited risk: fact\_type and

event\_type are unconstrained free strings with no classification layer,

and no field anywhere distinguished a directly-observed value from a

computed or estimated one. Phase 14 closes both, without changing the

free-string design or requiring any existing row to be reclassified.



\## FactClassification: advisory, not enforced

A new table maps a (applies\_to, type\_name) pair to a category and

description. It is deliberately NOT a foreign key from

FinancialFact.fact\_type or Event.event\_type - both remain free strings.

An unregistered type\_name is simply unclassified, not invalid; every

fact\_type and event\_type created in Phases 11-13 continues to work

unchanged, and future ones do not require pre-registration.



This is a conscious trade-off: a hard FK would give stronger guarantees

but would break backward compatibility with every already-shipped free

string. The advisory registry gets most of the classification value

(a lookup for "what kind of thing is 'dividend\_declared'") without that

cost.



\## observation\_kind: observed / derived / inferred

Added to both FinancialFact and Event as a required string column with

a database CHECK constraint, defaulting to "observed". This answers "is

this a directly sourced figure, a computed one, or an estimate" at the

row level - independent of fact\_type/event\_type, since the same type

string can be observed in one row and derived in another (e.g. a filed

"revenue" figure versus a forecast "revenue" estimate).



\## What this does NOT do

\- No derivation lineage: a "derived" or "inferred" row does not record

&#x20; which other facts or events produced it. That is a future Fact-to-Fact

&#x20; (or Fact-to-Event) relationship, not a precondition for this

&#x20; distinction to exist.

\- No validation that a "derived" fact actually has a computable basis,

&#x20; or that an "inferred" fact cites a model/method. observation\_kind is a

&#x20; label, not a proof.

\- No enforcement linking FactClassification to observation\_kind -

&#x20; the two are independent dimensions (a type can be classified and still

&#x20; have rows of any observation\_kind).



\## Migration

FactClassification is a new table, purely additive. observation\_kind is

a NEW NOT NULL column on two EXISTING tables (financial\_facts, events)

with a server\_default of 'observed', so existing rows (if any) are

backfilled automatically at column-add time, and no row needs its other

columns touched. Because this project has no Alembic, adding this column

still requires the same drop/recreate procedure Phase 12.1 used for

financial\_facts - see the implementation report for the pre-flight and

execution steps, gated on an explicit production data check for BOTH

financial\_facts and events before anything is dropped.

