# CapitalOS
# CapitalOS

CapitalOS is a structured reasoning and decision intelligence system. It helps
turn investment research into explicit, structured claims rather than
unstructured notes - so reasoning can be tracked, related, challenged, and
revisited over time.

The long-term vision includes Fundamental, Macro, Quant, Risk, and other
intelligence engines, plus a Challenger engine that critiques reasoning and a
human-only Decision layer. **None of that is implemented yet.** This README
describes only what currently exists.

## Current Scope

### Milestone 1 - Core Reasoning Objects
- **Entity** - a canonical subject (company, person, sector, country, asset,
  or other), so claims don't repeatedly store subject names as free text.
- **ResearchCase** - a container for reasoning about an entity, or about
  something broader than a single entity.
- **Claim** - the atomic unit of reasoning. Each claim has independent axes
  rather than one collapsed type:
  - `temporal_orientation`: historical / current / forecast
  - `epistemic_role`: evidence / interpretation / assumption / risk / hypothesis
  - `shape`: quantitative / qualitative
  - `confidence_band` (nullable): low / medium / high - deliberately not a
    percentage, to avoid false precision
  - `lifecycle_status`: active / superseded / invalidated / expired
  - `lens` (nullable): fundamental / macro / quant / strategic / risk / behavioural
  - `origin` (required): user / ai_suggested / engine_generated / imported

### Milestone 2 - Claim Relationships
- **ClaimRelationship** - a directed link between two claims:
  `relationship_type` is one of `supports`, `contradicts`, or `depends_on`.
- This is a plain relational table, not a graph database. The "Reasoning
  Graph" remains a computed view built from these rows, not a stored
  structure.
- A claim cannot relate to itself (`422`), and both claims referenced in a
  relationship must already exist (`404` if not).
- Relationships have no update endpoint by design - if a relationship is
  wrong, delete it and create the correct one, rather than editing it in
  place.

### Explicitly NOT implemented yet
- WorldData, ModelRun, Decision, Outcome
- The Challenger engine and ChallengeOutput
- Authentication
- Frontend
- Alembic migrations (schema is created via `Base.metadata.create_all()`)

## Tech Stack
- **Backend:** FastAPI + SQLAlchemy (declarative models) + Pydantic v2
- **Database:** PostgreSQL (Render-hosted). `DATABASE_URL` is fully
  environment-driven - no SQLite-specific logic in the application, so it
  would work against any Postgres instance.
- **Testing:** pytest, using an isolated test database
- **Deployment:** Render (Python 3 web service)

## Project Setup

### 1. Clone and enter the project
```cmd
git clone https://github.com/Vineeth2002/capitalos.git
cd capitalos\backend
```

### 2. Create and activate a virtual environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```cmd
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and set `DATABASE_URL`:
