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

```cmd
pytest -v
```

Live Gemini safety test is skipped by default (avoids burning free-tier
quota). To run it deliberately:

```cmd
set RUN_LIVE_LLM_TESTS=1
pytest -v
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

## Key URLs

- Local: http://127.0.0.1:8000
- Live: https://capitalos-bmdl.onrender.com
- GitHub: https://github.com/Vineeth2002/capitalos
- Render dashboard (web service): https://dashboard.render.com/web/srv-daejsm9t0dsc73ahnnf0
- Render dashboard (database): capitalos-db (free tier, expires Oct 6 2026 unless upgraded)
