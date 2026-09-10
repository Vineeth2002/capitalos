# CapitalOS — Developer Quick Reference

Personal reference for recurring local dev commands. Not part of the
application itself — safe to edit freely, nothing imports this file.

## Start the local server

```cmd
cd C:\capitalos\backend
C:\capitalos\backend\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open:
- http://127.0.0.1:8000/ (main reasoning workflow)
- http://127.0.0.1:8000/cases (Research Case list)
- http://127.0.0.1:8000/docs (Swagger UI, for direct API testing)
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

Current test count (as of Phase 9, commit cdfb458): 38 passed, 1 skipped.

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
the latest commit, or a deploy seems to have "succeeded" without the new
code actually showing up:

1. Render dashboard → `capitalos` web service
2. **Manual Deploy** → **Deploy latest commit**
3. Watch the **Logs** tab until you see `Shutting down` → `Finished server
   process` → a **new** `Started server process [PID]` → `Uvicorn running`
   → `Your service is live 🎉`
4. **Verify with curl, not just the dashboard.** Render's "live" status has
   been observed to appear before the new code was actually being served
   (Phase 9 hit this — the dashboard said the deploy was live, but `curl`
   kept returning the old HTML for 15+ minutes across multiple deploy
   attempts). Always confirm with:
```cmd
   curl -i "https://capitalos-bmdl.onrender.com/cases/4"
```
   Check `cf-cache-status` in the response headers - `DYNAMIC` means it's
   not a CDN cache issue, so if the content is still stale, the app process
   itself hasn't cycled yet. Trigger another Manual Deploy and wait again.

Restarting the web service (Manual Deploy, same code) also resets the
in-memory rate limiters (Challenger and Reasoning Intake, 5/hour each) to
0 — useful if you hit a limit yourself while testing. It does NOT touch the
Postgres database; all data survives a web service restart.

## Verify a deploy actually works
https://capitalos-bmdl.onrender.com/health
https://capitalos-bmdl.onrender.com/
https://capitalos-bmdl.onrender.com/cases


Walk through the actual UI flow (Analyze → review → Confirm → Challenge),
not just the health check — the health check does not exercise Gemini,
the database write path, or the frontend at all.

## Environment variables reference

`.env` (local, never commit — already in `.gitignore`):
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>/<database>
LLM_PROVIDER=gemini
LLM_MODEL=gemini-flash-latest
LLM_API_KEY=<your Gemini key>


Render web service needs the same three `LLM_*` vars plus
`DATABASE_URL` set under **Environment** in the dashboard (use the
Postgres **Internal** URL there, not External).

## Gemini quota — the recurring blocker

Google's Gemini free tier has TWO separate limits, both easy to hit during
active testing:
- **Per-minute:** 5 requests/minute
- **Per-day:** 20 requests/day, project-wide (shared across Challenger AND
  Reasoning Intake — every test, retry, and dogfooding session draws from
  the same 20)

**The daily quota resets at midnight Pacific Time, which is 12:30 PM IST**
(PDT is UTC-7, IST is UTC+5:30, a fixed 12.5-hour gap; India doesn't observe
DST so this offset is stable). This is a fixed daily clock time, not "N
hours after you first hit the limit."

Both limit types are caught in `challenger_service.py` and
`reasoning_intake_service.py` and surfaced as a clean `503 Service
Unavailable` — never a raw provider error. If you see that message
repeatedly, check the Render logs for a line starting with
`IntakeUnavailableError root cause:` or similar — this prints the actual
Gemini exception type (`ServerError` = outage, `ClientError` 429 = quota)
before it gets converted to the generic user-facing message.

If quota exhaustion keeps blocking testing or a live participant session,
the practical fix is enabling billing on the Gemini API project (Gemini
Flash pricing is a few cents per request at most) rather than waiting out
the daily reset — this is a reasonable trade given the value signal already
observed across multiple test domains.

## Known quirks

- **Swagger `case_id`/path-param fields auto-fill with the previous
  response's `id`.** Before executing any request, manually check and
  retype the path parameter — don't trust it to have stayed what you last
  typed. (This only matters when testing directly via `/docs`; the web UI
  handles this correctly.)
- **A request that fails still counts against the rate limit**, including a
  `404` before the Gemini call would even happen, and a Gemini `503`/`429`
  itself. Restarting the web service resets rate limiter state to 0 without
  touching data (see "Deploying to Render" above).
- **`venv\Scripts\activate.bat` may be empty/unreliable** on this
  machine — if activation silently does nothing, call
  `venv\Scripts\python.exe -m <tool>` directly instead (see above).
- **Copy-pasting rendered `<select>` dropdowns into chat/text tools often
  flattens all option text together** (e.g. "historical current forecast
  evidence..."), making a correctly-rendered dropdown look broken in pasted
  text. Always verify visually in the actual browser before treating this
  as a bug.

## Key URLs

- Local: http://127.0.0.1:8000
- Live: https://capitalos-bmdl.onrender.com
- GitHub: https://github.com/Vineeth2002/capitalos
- Render dashboard (web service): https://dashboard.render.com/web/srv-daejsm9t0dsc73ahnnf0
- Render dashboard (database): capitalos-db (free tier, expires Oct 6 2026 unless upgraded)
- Google AI Studio (Gemini key/usage): https://aistudio.google.com