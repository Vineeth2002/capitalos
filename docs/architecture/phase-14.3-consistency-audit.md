\# CapitalOS — Phase 14.3 Consistency \& Integrity Audit



\*\*Basis:\*\* checked against the exact file contents authored and committed

across Phases 11B-14 within this project's development history, not a

fresh repository scan (no live filesystem access exists in this

environment). Findings are labeled VERIFIED (confirmed against code

directly authored/recalled in full), INFERRED (reasoned from authored

code, not independently re-read), or UNVERIFIED (would require a fresh

file paste to confirm). No finding below is ASSUMED.



\---



\## 1. Entity / Company terminology drift



\*\*Checked:\*\* `app/models/entity.py` (unchanged since Milestone 1),

`app/models/security.py` (`issuer\_entity\_id` FK), `app/services/

security\_service.py` (`\_entity\_type\_value` check requiring

`entity\_type == 'company'`), `docs/architecture/

phase-12.1-focused-audit.md` ("Entity stays the general identity root...

No Company or Issuer table now").



\*\*Finding:\*\* No drift. Every file consistently treats "company" as an

`entity\_type` value on the general `Entity` table, never as a renamed or

parallel concept. `Security.issuer\_entity\_id` is named for its role

(issuer), not for a nonexistent `Company` table.



\*\*Status:\*\* INFERRED, no correction needed.



\---



\## 2. fact\_type / event\_type freedom vs. documented risk



\*\*Checked:\*\* `app/models/financial\_fact.py` (`fact\_type = Column(String,

...)`, no CHECK), `app/models/event.py` (`event\_type` same), `app/models/

fact\_classification.py` (advisory registry, no FK from either type

column), `tests/test\_fact\_classifications.py::

test\_unregistered\_fact\_type\_still\_works`, `docs/architecture/

phase-13-financial-events.md` and `phase-14-classification-and-

observation-kind.md` (both explicitly document this as a deliberate,

accepted trade-off).



\*\*Finding:\*\* No drift. The code matches its own documentation exactly —

free strings, advisory classification only, explicitly chosen to avoid

invalidating existing/future type values.



\*\*Status:\*\* INFERRED, no correction needed.



\---



\## 3. Schema-evolution gap between model definition and deployed schema



\*\*Checked:\*\* `app/models/financial\_fact.py` gained `observation\_kind` in

the same commit that added `Event`/`FactClassification`;

`Base.metadata.create\_all()` creates missing tables but never alters

existing ones; production `financial\_facts` (pre-existing since Phase

12.1) required a manual, separately-run `ALTER TABLE` to catch up, while

`events`/`fact\_classifications` (brand-new tables in that same deploy)

were created already-correct by `create\_all()`.



\*\*Finding:\*\* This is a real, structural hazard, not a one-off mistake —

it has now occurred twice (the Phase 12.1 `financial\_facts` drop/

recreate, and this Phase 14 `ALTER TABLE`), and will recur any time a

column is added to an \*\*existing\*\* table rather than a new one is

introduced. The project has no Alembic, so nothing currently prevents

a future column addition from being deployed as code while production

silently lags until someone remembers to run a manual migration

script. This is an operational pattern worth documenting explicitly as

a standing rule, not a defect to fix in any one file.



\*\*Status:\*\* VERIFIED against the exact deploy sequence that already

happened twice in this project.



\---



\## 4. Duplicated subject/reference validation logic



\*\*Checked:\*\* `app/services/financial\_fact\_service.py::

validate\_references` and `app/services/event\_service.py::

validate\_references` — both independently re-implement: entity/security/

listing existence checks, source/source\_record existence checks, and

the full supersession rule set (same subject, same type, not already

superseded).



\*\*Finding:\*\* The two functions are structurally identical, differing

only in which model (`FinancialFact` vs `Event`) and which type field

(`fact\_type` vs `event\_type`) they reference. This is a real maintenance

risk: a future correction to the supersession rule (for example,

allowing a second kind of exception) applied to one service function has

no guarantee of being applied to the other, and nothing in the test

suite would catch that drift, since each test file only tests its own

model.



\*\*Status:\*\* VERIFIED against the exact code authored for both services.

This is the kind of duplication worth consolidating into a shared

helper (e.g., a `subject\_validation.py` taking the model class and

type-field name as parameters) the next time either service needs a

real change — not urgent enough to justify a standalone refactor phase

on its own.



\---



\## 5. FactClassification.applies\_to enforcement level



\*\*Checked:\*\* `app/schemas/fact\_classification.py` (`ClassificationAppliesTo`

Pydantic enum, restricting API input to `"financial\_fact"`/`"event"`),

`app/models/fact\_classification.py` (`applies\_to = Column(String, ...)`,

no DB-level CHECK or enum).



\*\*Finding:\*\* Consistent with the project's established "advisory,

not enforced" pattern for `fact\_type`/`event\_type` — API callers are

constrained by Pydantic, but a row inserted directly via the ORM (as

several tests already do, e.g. `test\_database\_rejects\_invalid\_

observation\_kind\_on\_financial\_fact`) could set `applies\_to` to any

string. This mirrors `fact\_type`/`event\_type` exactly and was evidently

a deliberate, matching choice, not an oversight.



\*\*Status:\*\* INFERRED, no correction needed — consistent by design.



\---



\## 6. Event.source\_id has no ORM relationship — EventResponse.source is silently always null



\*\*Checked:\*\* `app/models/financial\_fact.py` includes `source =

relationship("ResearchSource")` at the end of the class (added

specifically to fix a bug found during Phase 11B testing, where

`FinancialFactResponse.source` was always `None` despite `source\_id`

being populated, because Pydantic's `from\_attributes` had no ORM

attribute to read). `app/models/event.py`, as authored in Phase 13, has

\*\*no equivalent relationship\*\* — only the bare `source\_id` column.

`app/schemas/event.py::EventResponse` nonetheless declares `source:

Optional\[ResearchSourceResponse] = None`, identical in shape to

`FinancialFactResponse.source`.



\*\*Finding:\*\* This is the exact same bug class already found and fixed

once in this project, now present again in a sibling model. Any `Event`

created with a real `source\_id` will, today, return `"source": null` in

its API response, even though the foreign key is correctly set and the

underlying `ResearchSource` row exists. `tests/test\_events.py` does not

catch this: `test\_source\_id\_and\_source\_record\_id\_validated` only checks

that invalid IDs are rejected (404), it never asserts that a \*valid\*

`source\_id` produces a populated `source` object in the response — unlike

`tests/test\_financial\_fact\_foundation.py::

test\_create\_fact\_with\_valid\_nullable\_source`, which explicitly asserts

`data\["source"]\["id"] == source\_id`. The missing relationship and the

missing test assertion are two halves of the same gap, and that is

exactly why it went unnoticed through 162 passing tests.



\*\*Status:\*\* VERIFIED against the exact `Event` model code authored and

committed in Phase 13 — this is a genuine, reproducible defect, not a

stylistic inconsistency.



\---



\## Decision Table



| # | Finding | Severity | Action |

|---|---|---|---|

| 1 | Entity/Company terminology | None found | No action |

| 2 | fact\_type/event\_type freedom | None found (by design) | No action |

| 3 | Schema-evolution gap (model vs. deployed schema) | Structural/operational risk | Document as a standing rule; no code change |

| 4 | Duplicated subject-validation logic | Maintenance risk | Defer consolidation until next real change to either service |

| 5 | FactClassification.applies\_to enforcement | None found (by design, consistent) | No action |

| 6 | `Event.source` relationship missing | \*\*Real bug\*\* | Requires correction before further Event-related work |



\## Classification



\*\*B. Minor inconsistencies — requires targeted correction, not a

redesign.\*\* Finding 6 is a genuine bug needing a fix (one line: add

`source = relationship("ResearchSource")` to `Event`, plus one assertion

added to `tests/test\_events.py` mirroring the existing FinancialFact

test). Finding 3 and 4 are real but are documentation/discipline items,

not code defects requiring immediate correction. Findings 1, 2, and 5

require no action at all.



\## Recommended next step (not executed in this pass, per instructions)

Fix Finding 6 only: add the missing relationship to `Event`, add the

missing test assertion, run the full suite locally, confirm no

regression, then decide separately whether that warrants its own small

commit or gets folded into whatever Phase 14.3 build work follows this

audit.

