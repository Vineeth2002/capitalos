# CapitalOS — Developer Quick Reference

Personal reference for recurring local dev commands. Not part of the
application itself — safe to edit freely, nothing imports this file.

## Start the local server

```cmd
cd C:\capitalos\backend
C:\capitalos\backend\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
C:\capitalos\backend\venv\Scripts\python.exe -m pip install psycopg2-binary
Only run it again if you recreate the virtual environment or get a missing psycopg2 error.


Then open:
- http://127.0.0.1:8000/docs (Swagger UI)
- http://127.0.0.1:8000/health

## Run tests

`pytest -v` alone may say "not recognized" (venv activation has been
unreliable on this machine). Use the same direct-call pattern as
uvicorn:

```cmd
C:\capitalos\backend\venv\Scripts\python.exe -m pytest -v
```

Live Gemini safety test is skipped by default (avoids burning free-tier
quota). To run it deliberately:

```cmd
set RUN_LIVE_LLM_TESTS=1
C:\capitalos\backend\venv\Scripts\python.exe -m pytest -v
```

## Creating/editing files (Windows terminal)

Simple new files:
```cmd
copy con path\to\file.py
[paste content]
[Enter, then Ctrl+Z, then Enter]
```

If `copy con` mangles the content (duplicated lines, broken quotes,
multi-line strings) — use Notepad instead, it's more reliable for
tricky pastes:
```cmd
notepad path\to\file.py
```
(Click "Yes" to create if it doesn't exist yet, paste, Ctrl+S, close.)

## Git workflow (after any change)

```cmd
git status
git add .
git commit -m "Describe the change"
git push origin main
```

`git status` first, always — to confirm `.env` (has live secrets) is
never staged.

## Deploying to Render

Render usually auto-deploys on push to `main`. If it doesn't pick up
the latest commit:
1. Render dashboard → `capitalos` web service
2. **Manual Deploy** → **Deploy latest commit**
3. Watch the **Logs** tab until you see `Uvicorn running` and
   "Your service is live"

Restarting the web service (Manual Deploy, same code) also resets the
in-memory Challenger rate limiter to 0/5 — useful if you hit the limit
yourself while testing. It does NOT touch the Postgres database; all
data survives a web service restart.

## Verify a deploy actually works

https://capitalos-bmdl.onrender.com/health
https://capitalos-bmdl.onrender.com/docs


Then run the same POST/GET workflow in Swagger as you would locally.

## Environment variables reference

`.env` (local, never commit — already in `.gitignore`):

DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>/<database>
LLM_PROVIDER=gemini
LLM_MODEL=gemini-flash-latest
LLM_API_KEY=<your Gemini key>


Render web service needs the same three `LLM_*` vars plus
`DATABASE_URL` set under **Environment** in the dashboard (use the
Postgres **Internal** URL there, not External).

## Known quirks

- **Swagger `case_id`/path-param fields auto-fill with the previous
  response's `id`.** Before executing any request, manually check and
  retype the path parameter (e.g. `case_id`) — don't trust it to have
  stayed what you last typed.
- **`/research-cases/{case_id}/challenge` is rate-limited to 5 requests
  per IP per hour.** A request that fails (404, or even a Gemini `503`)
  still counts against this limit. Restarting the web service resets
  it to 0/5 without touching your data (see Deploying to Render above).
- **Gemini `503` (high demand) after exhausted retries now returns a
  clean `503`** to the caller with a "temporarily unavailable" message,
  instead of a bare `500 Internal Server Error`.
- **`venv\Scripts\activate.bat` may be empty/unreliable** on this
  machine — if activation silently does nothing, call
  `venv\Scripts\python.exe -m <tool>` directly instead (see above).

## Key URLs

- Local: http://127.0.0.1:8000
- Live: https://capitalos-bmdl.onrender.com
- GitHub: https://github.com/Vineeth2002/capitalos
- Render dashboard (web service): https://dashboard.render.com/web/srv-daejsm9t0dsc73ahnnf0
- Render dashboard (database): capitalos-db (free tier, expires Oct 6 2026 unless upgraded)