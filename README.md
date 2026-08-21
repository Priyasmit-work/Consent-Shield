# ConsentShield — combined project

This folder contains both halves of ConsentShield, wired together:

```
ConsentShield/
  backend/    FastAPI service implementing the scan/preferences/apply-plan API
  frontend/   TanStack Start (React) popup UI that calls the backend for real
```

The frontend originally shipped with a fully mocked `api.ts` (no network
calls at all). It's now been rewired to call the real backend endpoints,
and the backend now sends CORS headers so the browser is allowed to call it.
What changed, concretely:

- **backend/app/main.py** — added `CORSMiddleware`, configured via a new
  `CORS_ORIGINS` env var (`backend/.env.example`), defaulting to the Vite
  dev server ports (`5173`, `3000`).
- **frontend/src/lib/consentshield/api.ts** — rewritten to make real `fetch`
  calls: `getScan()` POSTs `/api/v1/scans` and polls `GET /api/v1/scans/{id}`
  until it reaches a terminal status; `getSettings`/`saveSettings` call
  `GET`/`PUT /api/v1/me/preferences`; `applyPlan()` calls
  `POST /api/v1/scans/{id}/apply-plan`. Backend response shapes are mapped
  to the frontend's existing `ScanResult`/`Settings` types.
- **frontend/src/routes/index.tsx** — the popup now drives its screens off
  real API responses (loads preferences on mount, runs a real scan, applies
  a real protection plan) instead of static mock data. A URL input was
  added to `ScanIntro` since this is a web preview with no real browser tab
  to read a URL from.
- **frontend/.env.example** / **src/vite-env.d.ts** — new `VITE_API_BASE_URL`
  and `VITE_DEV_USER_ID` config.

## Running it locally

**1. Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # defaults are runnable with zero setup
cd backend
uvicorn app.main:app --reload --port 8000
```

Docs at http://localhost:8000/docs. Storage is in-memory by default (no
Supabase project required); auth defaults to `AUTH_MODE=dev`, which accepts
any `X-Dev-User-Id` header instead of a real token.

**2. Frontend**

```bash
cd frontend
cp .env.example .env          # points at http://localhost:8000 by default
npm install                   # or bun install
npm run dev                   # or bun run dev
```

Open the printed local URL. Enter a `https://` URL in the scan screen and
click **Scan privacy** — this now creates a real scan against the backend,
polls it to completion, and renders the real evidence/plan. Settings are
persisted to the backend's `/me/preferences` endpoint, and applying a
protection plan calls the backend's `/scans/{id}/apply-plan` endpoint (which,
per the backend's own safety rules, only actually "approves" an executable
plan when Settings → *Allow automatic protection* is on with a non-Manual
privacy mode — otherwise it correctly reports `awaiting_user_confirmation`,
which the popup now surfaces instead of pretending to execute).

**CORS**: if you serve the frontend from a different host/port than the
defaults above, add it to `CORS_ORIGINS` in `backend/.env`.

## Verified

- `npx tsc --noEmit` — passes with no errors.
- `npm run build` — production build succeeds.
- `pytest tests/ -q` — all 15 backend tests pass.
- Manual smoke test: CORS preflight, `POST /scans` → poll → `ready`,
  `GET`/`PUT /me/preferences`, and `POST /scans/{id}/apply-plan` were all
  exercised against a running server and match what `api.ts` expects.
