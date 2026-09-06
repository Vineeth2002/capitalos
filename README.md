# CapitalOS - Backend (Milestone 1)

CapitalOS is a structured reasoning and decision intelligence system. It is
being built incrementally; this repository currently implements **Milestone 1**
only.

## What CapitalOS Is

CapitalOS allows a user to:

1. Create an Entity (a company, person, sector, country, or asset).
2. Open a Research Case for that Entity.
3. Add structured Claims representing reasoning about that Entity.
4. View and update those Claims over time.

The long-term system is intended to eventually include additional
intelligence layers (fundamental, macro, quant, risk, and challenger
engines) and decision-tracking concepts (Decision, Outcome). **None of
that is implemented yet.** This README describes only what currently
exists in code.

## Milestone 1 Scope

Implemented:

- `Entity` - canonical subject records (company, person, sector, country,
  asset, other)
- `ResearchCase` - a container for structured reasoning, optionally tied
  to an Entity
- `Claim` - the atomic unit of reasoning, with independent axes:
  `temporal_orientation`, `epistemic_role`, `shape`, `confidence_band`,
  `lifecycle_status`, `lens`, and `origin`

Not implemented yet (intentionally out of scope for Milestone 1):

- WorldData, ModelRun, Decision, Outcome
- Challenger engine / ChallengeOutput
- Claim-to-Claim relationships or a Reasoning Graph as a stored primitive
- Authentication
- Frontend## Project Setup

### Prerequisites

- Python 3.10+

### Install dependencies

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

```cmd
copy .env.example .env
```

| Variable       | Description                                   | Default                        |
|----------------|------------------------------------------------|---------------------------------|
| `DATABASE_URL` | SQLAlchemy connection string. SQLite for local development; PostgreSQL-compatible for later environments. | `sqlite:///./capitalos.db` |

## How to Run Locally

```cmd
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`. Database tables are created
automatically on startup via `Base.metadata.create_all()`.## API Documentation

Interactive Swagger documentation is available at:

http://127.0.0.1:8000/docs


A basic health check is available at:

http://127.0.0.1:8000/health


## Running Tests

```cmd
pytest -v
```

Tests use an isolated SQLite database (`test.db`) and cover Entity
creation, Research Case creation, Claim creation, Claim enum validation,
and Claim-to-ResearchCase ownership.
