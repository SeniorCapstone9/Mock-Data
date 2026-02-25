# Project Status (Capstone / RunPod / Notifications)

Date: 2026-02-25

## Executive Summary

The project is currently in a usable development state on RunPod.

- The app can be opened in browser
- Admin login works
- The notification system works end-to-end in the UI
- Core backend/frontend integration issues for RunPod dev were fixed

The biggest remaining technical issue is storage quota on `/workspace`, which prevents full installation of the heavy ML backend dependencies (Whisper / Pyannote / PaddleOCR stack).

## What Has Been Achieved

### A) RunPod development workflow is now workable

- `/workspace` was confirmed as the persistent mount
- Persistence helpers were added so root-owned tool/cache data can survive pod resets:
  - `scripts/runpod_persist_setup.sh`
  - `scripts/runpod_project_setup.sh`
- Root directories now symlink to `/workspace/persist` (when setup script is run), including:
  - `.vscode-server`
  - `.ollama`
  - `.nvm`
  - `.cache`
  - `.npm`

### B) Frontend-backend connectivity on RunPod was fixed

The frontend originally failed in browser because it tried to call `localhost:8002` from the user’s browser.

Fixes made:
- `client/src/config.js`
  - Uses relative API paths on non-localhost hosts
- `client/vite.config.js`
  - Vite proxy added for `/api`, `/token`, `/temp`, `/docs`, `/openapi.json`
- `client/src/App.jsx`
  - Removed remaining hardcoded backend URLs for delete actions
- `client/src/components/Login.jsx`
  - Cleaner error messaging (not misleadingly hardcoded to port `8002`)

Result:
- Frontend on `5173` can talk to backend on `8002` through Vite proxy
- Only frontend port needs browser exposure in RunPod for dev

### C) Backend login is working

Login initially failed due to a `passlib` + `bcrypt` compatibility issue.

Fix:
- Temporary backend venv (`/tmp/demoSTT-api`) was patched with:
  - `bcrypt==4.0.1`

Result:
- Admin login works in browser

### D) Notification system is working end-to-end (major milestone)

Notification backend routes were restored/re-added to `server/main.py` after `main.py` had to be recovered from Git.

Working and verified:
- Import visits (JSON)
- Import visits (CSV)
- Run notification engine
- Notification feed list
- Notification detail view
- Distribution skew data
- Send notification
- Delivery history

UI is working in:
- `client/src/components/Notifications.jsx`

### E) Notification engine logic is implemented and explainable

Implemented in `server/notification_engine.py`:
- Groups by `(date, location)`
- Counts total visits
- Counts symptom occurrences
- Computes rate = `symptom_count / total_visits`
- Threshold severities:
  - `info >= 0.15`
  - `warning >= 0.30`
  - `critical >= 0.50`
- Upserts notification rows into SQLite

The system is explainable because notifications include:
- symptom count
- total visits
- rate
- threshold used
- severity

## Current Working Areas

### Working now

- Frontend UI and routing
- Authentication/login
- Core admin/dashboard browsing
- Notification system (import/run/feed/detail/send/history)
- SQLite storage for notification data

### Partially working / not fully available

- Audio transcription pipeline (likely blocked by missing heavy ML deps)
- OCR pipeline (same reason)
- Ollama-related AI features (binary not installed in current session)

## Known Issues / Needs Improvement

### 1) `/workspace` quota is the main blocker

Problem:
- Full backend dependency install fails with `Disk quota exceeded`
- Heavy packages (`torch`, CUDA wheels, pyannote, paddleocr) exceed available quota

Impact:
- Persistent full backend environment cannot be completed
- AI/OCR features are not reliable in current pod setup

Recommended next action:
- Increase RunPod persistent storage/quota OR free space aggressively
- Then finish persistent backend install in `/workspace/persist/venvs/demoSTT`

### 2) Runtime today depends on temporary `/tmp` tools

Currently used for development:
- Backend venv: `/tmp/demoSTT-api`
- Node 22: `/tmp/node22`

Impact:
- These disappear after pod/container reset

Recommended next action:
- Make a reusable startup/bootstrap script that recreates temp runtime quickly
- Or install a persistent Node runtime under `/workspace/persist/bin`
- Or use a custom RunPod image

### 3) `server/main.py` may need re-merge of lost edits

`server/main.py` was accidentally truncated during an edit and restored from Git `HEAD`, then patched.

Risk:
- Any uncommitted custom edits that were not in Git may be missing

Recommended next action:
- Compare current `server/main.py` with your expected/latest version
- Reapply any missing changes from IDE local history if needed

## Notification System: Professor Spec Alignment Status

### Already aligned

- End-to-end demo-safe prototype
- Mock/simulated data support
- Explainable decision logic
- SQLite persistence
- Dashboard feed/detail/distribution view
- No PII in notification messages

### Differences from spec (mostly naming/polish)

- Input table name is `notification_visits` instead of `visit_records`
- Output date field is `group_date` instead of `date_window`
- `location` uses state codes (`FL`) instead of full state names (`Florida`)
- Engine currently alerts on all symptoms, not just flu (spec MVP suggests starting with flu)
- API path prefix uses `/api/...`

### Recommended “professor-alignment pass”

1. Add flu-only mode (or default focus on flu)
2. Add compatibility aliases/mapping for `visit_records` + `date_window`
3. Standardize message wording to match professor example
4. Optionally aggregate distribution as `flu/fever/cough/other`
5. Add CLI runner for engine (manual demo command)

## What Needs Working On Next (Priority Order)

### High priority

1. Commit current working changes
2. Stabilize restart workflow after pod reset
3. Resolve `/workspace` quota issue

### Medium priority

4. Professor-aligned notification polish (flu-first, naming, message format)
5. Add automated acceptance test script for notification flow

### Lower priority

6. Restore full AI/OCR stack
7. Improve deployment/startup automation for RunPod

## Suggested Demo Narrative (Current System)

1. Log into admin dashboard
2. Open Notifications
3. Import mock data (JSON or CSV)
4. Run engine
5. Show alert feed
6. Click a critical Florida flu alert
7. Explain:
   - total visits
   - symptom count
   - rate
   - threshold
   - severity
8. Show distribution skew table
9. Send notification and show delivery history

## Files Most Important for Next Development

- `server/main.py`
- `server/notification_engine.py`
- `server/notification_delivery.py`
- `server/database.py`
- `client/src/components/Notifications.jsx`
- `client/src/config.js`
- `client/vite.config.js`
- `scripts/runpod_persist_setup.sh`
- `scripts/runpod_project_setup.sh`
- `docs/SESSION_HANDOFF.md`

