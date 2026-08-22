# ConsentShield — Setup & webcmd Integration Notes

This README documents the current local setup for ConsentShield
(FastAPI backend + TanStack Start frontend + `webcmd` live browser
driver), what was changed to wire live scanning and live execution
together, and how to run everything.

```
ConsentShield/
  backend/
    backend/app/     FastAPI service (scan, preferences, apply-plan API)
    .venv/           Python virtual environment
    .env             Backend config (WEBCMD_MODE, CORS, auth mode, etc.)
  frontend/           TanStack Start (React) UI that calls the backend
```

The `webcmd` CLI itself lives in a separate folder outside this
project (wherever you extracted `webcmd-main.zip`), and is installed
onto `PATH` globally via `npm link`.

---

## 1. Running the backend

```powershell
cd ConsentShield\backend\backend
..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Storage is in-memory by default (no Supabase project required).
- Auth defaults to `AUTH_MODE=dev`, which accepts any `X-Dev-User-Id`
  header instead of a real token.

If the venv doesn't exist yet:

```powershell
cd ConsentShield\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## 2. Running the frontend

```powershell
cd ConsentShield\frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open http://localhost:5173. If `.env` doesn't exist yet:

```powershell
Copy-Item .env.example .env
```

It points `VITE_API_BASE_URL` at `http://localhost:8000` by default.

## 3. Setting up webcmd (live browser driver)

```powershell
cd path\to\webcmd-main\ConsentShield-main\webcmd
npm install --ignore-scripts
npm run build
npm link --ignore-scripts
webcmd --version   # should print a version number, e.g. 0.7.4
```

`--ignore-scripts` is needed on Windows because the package's `prepare`
script uses a Unix-only shell check (`[ -d src ] && ...`) that `cmd.exe`
doesn't understand. The manual `npm run build` step does the same work
without relying on that check.

In `backend/.env`, set:

```
WEBCMD_MODE=live
```

If `webcmd` isn't resolvable on `PATH` from inside the Python process,
set an explicit path instead:

```
WEBCMD_BIN=C:\path\to\webcmd\dist\src\main.js
```

**Restart the backend after any `.env` change** — environment variables
are only read once at process startup.

---

## 4. What was changed to wire webcmd in

The project originally shipped with `WEBCMD_MODE=live` as an
unimplemented "integration seam" — the toggle existed in `.env` but no
code path actually called `webcmd`. The following two integration
points were added:

### a) Live banner detection (`browser_agent.py`)

`BrowserAgentService.run_scan` now calls
`webcmd_client.scan_cookie_banner(url)` when `WEBCMD_MODE=live`,
instead of only ever fabricating mock evidence. It:

- Navigates to the target URL in a fresh `webcmd` session.
- Detects the consent-banner iframe (Sourcepoint, OneTrust, Cookiebot,
  Didomi, Quantcast, TrustArc, or any frame matching `consent`/`cmp`).
- Extracts the real button labels and any cookie/privacy policy links
  found inside it.
- Falls back to the existing mock evidence path (with a logged
  warning) if `webcmd` isn't installed, times out, or errors — a scan
  never hard-fails just because live browsing didn't work.

Real button labels are then matched (by keyword) onto the
`accept_all` / `reject_optional` / `manage_preferences` actions the
rest of the app expects, instead of always using hardcoded label text.

### b) Live execution (`execution.py` + `webcmd_client.py`)

A new `click_banner_action(url, button_label)` function was added to
`webcmd_client.py`. It opens a fresh `webcmd` session, re-locates the
same consent banner, and clicks whichever button's text matches the
approved plan's label (exact match, then substring fallback).

`POST /scans/{id}/apply-plan` now calls this function **only after**
the backend's own existing approval rules are satisfied — this route's
"must not click a consent button by default" safety rule (Section 8 of
the original design) was **not changed**. Concretely, a live click is
only attempted when:

1. `preferences.auto_apply` is `True`, **and**
2. the user's selected privacy mode is not `Manual`, **and**
3. `WEBCMD_MODE=live`.

If any of those aren't true, the endpoint still returns
`awaiting_user_confirmation` exactly as before, and no click is ever
attempted. This preserves the original "never silently act on the
user's behalf" guarantee — it only adds a real execution path for the
case that was already meant to be automatic.

**Important caveat:** the live click happens inside `webcmd`'s own
headless browser session, not in the user's own visible browser tab.
It proves the backend can drive a real consent choice against the real
site, but it will not visibly change anything in your own Chrome
window. A true "changes cookies in the tab I'm looking at" experience
would require a real browser extension content script reading the
approved plan's `allowed_locators` and clicking in-page — that's a
separate, bigger piece of work than what's wired up here.

---

## 5. Known open item

As of this writing, applying a protection plan from the UI still
returns `awaiting_user_confirmation` ("Confirm in the extension before
changing cookie consent") even after selecting a non-Manual privacy
mode (e.g. Strict). This means `preferences.auto_apply` is still
`False` on the backend — privacy mode and the auto-apply toggle are
two separate settings. There should be a separate "Allow automatic
protection" switch elsewhere in the Settings screen; its state (and
whether the frontend is actually sending `auto_apply: true` when
saving preferences) still needs to be confirmed before a live click
will ever be attempted.

To check directly against the backend:

```powershell
curl http://localhost:8000/api/v1/me/preferences -H "X-Dev-User-Id: demo-user"
```

Look for `"auto_apply"` in the response — if it's `false`, that's the
setting to fix, either in the UI or via:

```powershell
curl -X PUT http://localhost:8000/api/v1/me/preferences `
  -H "X-Dev-User-Id: demo-user" `
  -H "Content-Type: application/json" `
  -d '{"auto_apply": true, "privacy_mode": "strict"}'
```

(Adjust the body to match whatever fields `PreferencesRepository`
actually expects — check `app/schemas/preferences.py` if this 422s.)
