# ConsentShield Backend

A privacy-first FastAPI backend implementing the ConsentShield API contract:
cookie-banner/privacy-policy analysis, evidence-backed recommendations, and a
short-lived, hostname-bound execution plan for a browser extension.

Operating principle: **Detect -> Analyze -> Recommend -> Confirm -> Execute -> Report.**
Default behavior is read-only; automatic protection is disabled unless the
user's preferences explicitly enable it (`auto_apply: true`, mode != `manual`).

This implements **only** the backend described in the two authoritative
documents:
- the API contract (endpoints, request/response shapes, DB schema, safety rules)
- `consentshield-extension-prd.md` (product intent, scope, acceptance criteria)

The browser extension itself (Manifest V3 popup / service worker / content
script) is out of scope for this repo.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # defaults are runnable with zero setup
cd backend
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the generated OpenAPI docs.

Run the tests:

```bash
pytest tests/ -q
```

## What's real vs. what's a reference implementation

This is a hackathon MVP, and two pieces genuinely cannot be "real" without
external infrastructure the spec doesn't provide credentials for. Both are
implemented behind clean, swappable interfaces so replacing them does not
touch the rest of the backend:

| Piece | Default (this repo) | How to go live |
|---|---|---|
| **webcmd browser agent** (`services/browser_agent.py`) | `WEBCMD_MODE=mock` — a deterministic exploration simulation that drives the full scan lifecycle (`queued -> exploring -> extracting -> analyzing -> ready`), fabricates plausible per-category evidence tied to the real target hostname, and demonstrates workflow reuse on a second scan of the same site. It does **not** claim to have inspected the live site's real policy text. | Set `WEBCMD_MODE=live` and implement `_explore_live` with a real webcmd client. |
| **Model adapter** (`services/model_service.py`) | `MODEL_MODE=heuristic` — a keyword-based classifier that only ever reasons over the evidence excerpts it's given (never outside knowledge), and returns `unknown` when evidence is absent. | Set `MODEL_MODE=live` + `MODEL_API_URL` to call a real model behind the same `CookieRiskClassificationV1` JSON contract (see `prompts/cookie_privacy_analysis.txt`). |
| **Storage** (`repositories/`) | In-memory, process-local. Runs with zero setup. | Set `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`; the same repository classes switch to Supabase automatically (schema in `supabase/migrations/001_initial_schema.sql`, RLS enforced via `auth.uid()`). |
| **Auth** (`dependencies.py`) | `AUTH_MODE=dev` — accepts a `X-Dev-User-Id` header. Only active when `ENVIRONMENT=hackathon`; refuses to run in any other environment. | Set `AUTH_MODE=supabase_jwt` + `SUPABASE_JWT_SECRET` to verify real Supabase-issued bearer tokens. |

Neither uploaded document specifies a concrete auth token format, so the dev
header is a minimal, clearly-labeled placeholder — not a hidden assumption.

## Endpoints implemented

```
GET    /api/v1/health
GET    /api/v1/me/preferences
PUT    /api/v1/me/preferences
POST   /api/v1/scans
GET    /api/v1/scans/{scan_id}
POST   /api/v1/scans/{scan_id}/apply-plan
POST   /api/v1/scans/{scan_id}/events
DELETE /api/v1/scans/{scan_id}
GET    /api/v1/sites/{site_key}/latest
```

## Safety behavior worth knowing about

- **`PUT /me/preferences` rejects contradictions with 422**, rather than
  silently correcting them: `categories.essential = false`,
  `categories.unknown = true`, or `auto_apply = true` while `mode = manual`.
- **`POST /scans/{id}/apply-plan` never hands back an executable plan unless
  the user's preferences have `auto_apply: true`** — this is the literal rule
  stated in the contract ("must not directly click a consent button by
  default"). Otherwise it always returns `awaiting_user_confirmation`,
  regardless of the `confirmation` flag in the request body.
- Execution plans are **hostname-bound**: if the `client_context.page_url`
  hostname doesn't match the scan's original hostname, the request is
  rejected with 422 rather than silently applied to the wrong site.
- `POST /scans/{id}/events` uses a strict Pydantic schema (`extra="forbid"`)
  so it can only ever accept `action` / `success` / `message` — never
  cookies, auth headers, DOM snapshots, or form values.
- Unknown categories are never included in `allowed_categories`, in any
  privacy mode, regardless of what a `custom` preference set contains.

## Project layout

```
backend/app/
  api/v1/routes/     - one module per endpoint group
  schemas/           - Pydantic request/response models + validation
  services/          - browser agent, model adapter, analyzer, planner
  repositories/      - Supabase-or-in-memory storage behind one interface
  prompts/           - live-model prompt template
supabase/migrations/ - schema + RLS, copied from the API contract
tests/               - preferences validation, full scan lifecycle, analyzer
```
