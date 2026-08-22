# ConsentShield

**ConsentShield** is a privacy-first tool that scans cookie/consent banners for
dark patterns, explains what a site is really asking for, and (with explicit
user opt-in) automatically applies the privacy-safe choice.

---

## Screenshots

| Landing / Scan View | Preferences / Protection Plan |
|---|---|
| <img width="1917" height="907" alt="Screenshot 2026-08-22 122540" src="https://github.com/user-attachments/assets/7d3d5f74-6286-425f-bcd2-4804d896dd20" />
 | <img width="540" height="717" alt="ConsentShield 1" src="https://github.com/user-attachments/assets/0793a659-b951-4ad0-b71e-df7f98f65fc4" />
 |



---

## System Architecture

```
                         ┌───────────────────────────┐
                         │        User Browser        │
                         │  (React / TanStack Start)  │
                         └──────────────┬──────────────┘
                                        │ HTTPS (fetch/JSON)
                                        ▼
                         ┌───────────────────────────┐
                         │       FastAPI Backend      │
                         │   (Python / Uvicorn ASGI)  │
                         │                            │
                         │  api/v1/routes             │
                         │   ├─ scans                 │
                         │   ├─ preferences            │
                         │   ├─ execution (apply-plan) │
                         │   ├─ events                 │
                         │   └─ health                 │
                         │                            │
                         │  services/                 │
                         │   ├─ browser_agent          │──┐
                         │   ├─ cookie_detector         │  │
                         │   ├─ privacy_analyzer         │  │  triggers live scan
                         │   ├─ policy_finder            │  │
                         │   ├─ protection_planner       │  │
                         │   ├─ model_service (LLM)      │  │
                         │   └─ webcmd_client             │  │
                         └───────────────┬────────────┘  │
                                        │                │
                     ┌──────────────────┼────────────────┘
                     ▼                  ▼
         ┌───────────────────┐  ┌──────────────────────┐
         │      Supabase       │  │        webcmd          │
         │   (Postgres DB)     │  │  Headless browser CLI  │
         │  scans, preferences,│  │  (detects & clicks real │
         │  events tables       │  │   consent banners on   │
         └───────────────────┘  │   live target sites)    │
                                 └──────────────────────┘
                     │
                     ▼
         ┌───────────────────┐
         │   LLM Provider      │
         │ (cookie/privacy-    │
         │  policy analysis    │
         │  via model_service) │
         └───────────────────┘
```

### Flow

1. **User submits a URL** from the frontend → `POST /api/v1/scans`.
2. **`browser_agent`** launches a scan. If `WEBCMD_MODE=live`, it calls
   `webcmd_client.scan_cookie_banner(url)`, which drives a real headless
   browser session via the `webcmd` CLI to locate the consent banner
   (Sourcepoint, OneTrust, Cookiebot, Didomi, Quantcast, TrustArc, or any
   `consent`/`cmp`-matching frame) and extract real button labels and
   policy links. If `webcmd` is unavailable or times out, it falls back to
   mock evidence so a scan never hard-fails.
3. **`cookie_detector`** and **`policy_finder`** parse the extracted
   evidence; **`privacy_analyzer`** (backed by **`model_service`**, an
   LLM call using the prompt in `app/prompts/cookie_privacy_analysis.txt`)
   evaluates the banner and policy text for dark patterns and risk.
4. **`protection_planner`** turns the analysis into a proposed action
   plan (e.g. "reject non-essential cookies").
5. Results are persisted via the **repositories** layer to **Supabase**
   (`scans`, `preferences`, `events` tables — in-memory storage is used
   instead when no Supabase project is configured, for local dev).
6. The frontend polls/fetches scan results and renders findings +
   recommended actions.
7. **Applying a plan** (`POST /scans/{id}/apply-plan`) only triggers a
   real click via `webcmd_client.click_banner_action()` when **all** of
   the following hold: `preferences.auto_apply = true`, the privacy mode
   is not `Manual`, and `WEBCMD_MODE=live`. Otherwise the API returns
   `awaiting_user_confirmation` and nothing is clicked — the app never
   silently acts on the user's behalf.

---

## Tech Stack

**Frontend:** React 19 + TanStack Start (Vite), TypeScript, Tailwind CSS v4,
shadcn/ui on Radix primitives, TanStack Query, React Hook Form + Zod

**Backend:** FastAPI (Python), Uvicorn, Pydantic v2, PyJWT, httpx, pytest

**Data:** Supabase (Postgres), with in-memory fallback storage for local dev

**AI:** LLM-based cookie/privacy-policy analysis (`model_service.py` +
`prompts/cookie_privacy_analysis.txt`)

**Automation:** `webcmd` — a standalone CLI that drives a real headless
browser to detect and click cookie-consent banners on live sites

---

## Folder Structure

```
ConsentShield/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── backend/
│   │   └── app/
│   │       ├── main.py                  # FastAPI app entrypoint, CORS, error handlers
│   │       ├── config.py                # Settings (env vars, WEBCMD_MODE, CORS, auth mode)
│   │       ├── dependencies.py
│   │       ├── api/
│   │       │   └── v1/
│   │       │       ├── router.py
│   │       │       └── routes/
│   │       │           ├── scans.py          # POST/GET /scans
│   │       │           ├── preferences.py    # user privacy preferences
│   │       │           ├── execution.py      # POST /scans/{id}/apply-plan
│   │       │           ├── events.py
│   │       │           └── health.py
│   │       ├── services/
│   │       │   ├── browser_agent.py      # orchestrates a scan (mock or live)
│   │       │   ├── cookie_detector.py
│   │       │   ├── privacy_analyzer.py   # LLM-backed analysis
│   │       │   ├── policy_finder.py
│   │       │   ├── protection_planner.py # builds the action plan
│   │       │   ├── model_service.py      # LLM API calls
│   │       │   └── webcmd_client.py      # talks to the webcmd CLI
│   │       ├── repositories/
│   │       │   ├── supabase_client.py
│   │       │   ├── scans_repository.py
│   │       │   ├── preferences_repository.py
│   │       │   └── events_repository.py
│   │       ├── schemas/
│   │       │   ├── common.py
│   │       │   ├── scans.py
│   │       │   ├── preferences.py
│   │       │   ├── execution.py
│   │       │   └── events.py
│   │       └── prompts/
│   │           └── cookie_privacy_analysis.txt
│   ├── supabase/
│   │   └── migrations/
│   │       └── 001_initial_schema.sql
│   └── tests/
│       ├── conftest.py
│       ├── test_preferences.py
│       ├── test_privacy_analyzer.py
│       └── test_scan_schema.py
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── .env.example
    ├── public/
    └── src/
        ├── router.tsx
        ├── server.ts
        ├── start.ts
        ├── styles.css
        ├── routes/
        │   ├── __root.tsx
        │   └── index.tsx
        ├── components/
        │   ├── cs/                      # ConsentShield-specific components
        │   │   ├── header.tsx
        │   │   ├── screens.tsx
        │   │   ├── edge-states.tsx
        │   │   └── primitives.tsx
        │   └── ui/                      # shadcn/ui component library
        ├── hooks/
        │   └── use-mobile.tsx
        └── lib/
            ├── consentshield/
            │   ├── api.ts               # API client for the FastAPI backend
            │   └── types.ts
            └── utils.ts
```

---

## Running Locally

### Backend

```bash
cd backend/backend
python -m venv .venv
source .venv/bin/activate        # .venv\Scripts\Activate.ps1 on Windows
pip install -r ../requirements.txt
cp ../.env.example ../.env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`. `.env` points `VITE_API_BASE_URL` at
`http://localhost:8000` by default.

### webcmd (optional, for live banner scanning)

```bash
cd path/to/webcmd
npm install --ignore-scripts
npm run build
npm link --ignore-scripts
webcmd --version
```

Set `WEBCMD_MODE=live` in `backend/.env` to enable it (restart the backend
after changing `.env`).

---

## Safety Notes

- Scans are **read-only by default**.
- Automatic clicking of a consent button only happens when the user has
  explicitly enabled `auto_apply` **and** selected a non-`Manual` privacy
  mode **and** `WEBCMD_MODE=live` — otherwise the API always returns
  `awaiting_user_confirmation`.
- Live clicks currently execute inside `webcmd`'s own headless session,
  not the user's visible browser tab; a browser-extension content script
  would be needed for in-page actions on the user's real tab.
