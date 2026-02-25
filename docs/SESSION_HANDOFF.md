# Session Handoff (RunPod / Notification System)

Date: 2026-02-25

## What Was Achieved

- Frontend and backend are running for development on RunPod.
- Admin login works.
- Notification system works end-to-end in UI:
  - import JSON visits
  - import CSV visits
  - run engine
  - list alerts
  - view alert details
  - view distribution skew
  - send notification
  - view delivery history

## Key Fixes Made

### 1) RunPod persistence helpers added

- `scripts/runpod_persist_setup.sh`
  - Symlinks root-owned tool/cache dirs to `/workspace/persist`
  - Persists `.vscode-server`, `.ollama`, `.nvm`, `.cache`, `.npm`, etc.
- `scripts/runpod_project_setup.sh`
  - Creates persistent venv at `/workspace/persist/venvs/demoSTT`
  - Links `server/.venv` to it
  - Installs project deps (uses `--no-cache-dir` for pip)

### 2) Frontend API connectivity fixes (RunPod-safe)

- `client/src/config.js`
  - Uses relative API URL on non-localhost hosts (RunPod/browser access)
- `client/vite.config.js`
  - Added Vite proxy for `/api`, `/token`, `/temp`, `/docs`, `/openapi.json`
- `client/src/App.jsx`
  - Replaced hardcoded delete URLs with `API_URL`
- `client/src/components/Login.jsx`
  - Removed hardcoded port wording in error messages

### 3) Backend startup + login fixes

- `server/main.py`
  - AI/OCR imports made lazy so backend can start without full ML stack installed
  - Notification API routes restored (after `main.py` had to be restored from Git)
- Temporary backend venv in `/tmp/demoSTT-api`
  - Core API deps installed for dev startup
  - `bcrypt` pinned to `4.0.1` to fix `passlib` login crash

### 4) Notification system restored in backend

Notification routes added/restored in `server/main.py`:

- `POST /api/notification-visits/import`
- `POST /api/notification-visits/import-csv`
- `POST /api/notifications/run`
- `GET /api/notifications`
- `GET /api/notifications/{id}`
- `GET /api/notifications/{id}/distribution`
- `GET /api/notifications/{id}/deliveries`
- `POST /api/notifications/{id}/send`

## Important Current Limitations

### Storage quota issue (major)

- `/workspace` quota fills up during full ML dependency install.
- Full backend ML stack (`torch`, `pyannote`, `paddleocr`, etc.) is not fully installed in persistent venv.
- Result: transcription/OCR/AI features may fail.

### Session-only runtime tools

The currently running dev setup depends on temporary installs in `/tmp`:

- Backend venv: `/tmp/demoSTT-api`
- Node 22 binary: `/tmp/node22`

These will disappear when the pod/container resets.

### `server/main.py` recovery note

- `server/main.py` was restored from Git `HEAD` after accidental truncation.
- Notification routes were re-added.
- If there were uncommitted changes in `server/main.py` before recovery, they may need manual re-merge.

## Notification System Logic (Current)

Implemented in `server/notification_engine.py`:

- Group visits by `(date, location)`
- Count `total_visits`
- Count each symptom occurrence within group
- Compute `rate = symptom_count / total_visits`
- Severity thresholds:
  - `info >= 0.15`
  - `warning >= 0.30`
  - `critical >= 0.50`
- Upsert notifications into SQLite

Notes:
- It currently alerts on all symptoms, not only flu.
- Symptoms are normalized (`influenza` -> `flu`, etc.).

## Professor Spec Alignment (Quick Summary)

### Already aligned

- End-to-end demo-safe prototype
- Mock data support
- Explainable alerts (counts + rate + threshold)
- Simple rule-based logic
- SQLite storage
- Dashboard feed + detail + skew view

### Partially aligned / naming differences

- Input table name is `notification_visits` (spec says `visit_records`)
- Output fields use `group_date` (spec says `date_window`)
- Location uses state code (`FL`) instead of full state text (`Florida`)
- Alerts can trigger for all symptoms (spec MVP suggests starting with flu)

## How To Restart In A New Session (Fastest Path)

### 1) Re-run persistence setup (safe)

```bash
cd /workspace/demoSTT
bash scripts/runpod_persist_setup.sh
source /workspace/persist/runpod_env.sh
```

### 2) Start backend (current working dev mode)

This uses the temporary venv approach (until persistent full install is fixed):

```bash
/tmp/demoSTT-api/bin/uvicorn main:app --host 0.0.0.0 --port 8002
```

If `/tmp/demoSTT-api` is missing after reset, recreate it:

```bash
python3 -m venv /tmp/demoSTT-api
/tmp/demoSTT-api/bin/pip install --no-cache-dir fastapi==0.109.2 uvicorn[standard]==0.27.1 sqlalchemy==2.0.27 python-multipart==0.0.9 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-dotenv==1.0.1 pydantic==2.12.5
/tmp/demoSTT-api/bin/pip install --no-cache-dir bcrypt==4.0.1
```

### 3) Start frontend (Vite) with Node 22 in `/tmp`

Ubuntu `apt` installs Node 12, which is too old for Vite in this repo.

Install temp Node 22:

```bash
cd /tmp
curl -fsSLO https://nodejs.org/dist/latest-v22.x/node-v22.22.0-linux-x64.tar.xz
rm -rf /tmp/node22 && mkdir -p /tmp/node22
tar -xJf node-v22.22.0-linux-x64.tar.xz -C /tmp/node22 --strip-components=1
```

Run frontend:

```bash
export PATH=/tmp/node22/bin:$PATH
cd /workspace/demoSTT/client
npm run dev -- --host 0.0.0.0 --port 5173
```

### 4) RunPod exposure

- Expose/forward frontend port `5173`
- Backend port `8002` does not need browser exposure during dev because Vite proxy forwards API calls

## Suggested Next Work

1. Commit current working changes (especially `server/main.py` + frontend proxy/config)
2. Reconcile any lost custom edits in `server/main.py`
3. Make notification system exactly professor-aligned:
   - flu-only mode
   - spec naming compatibility (`visit_records`, `date_window`)
   - exact message format
   - optional CLI engine runner
4. Resolve `/workspace` quota so persistent backend ML stack can install fully

## Files Most Relevant Next Session

- `server/main.py`
- `server/notification_engine.py`
- `server/notification_delivery.py`
- `server/database.py`
- `client/src/components/Notifications.jsx`
- `client/src/config.js`
- `client/vite.config.js`
- `scripts/runpod_persist_setup.sh`
- `scripts/runpod_project_setup.sh`

## Recommended “Memory” Files For New Chats

These files were added specifically to help future chat sessions recover context faster:

- `docs/SESSION_HANDOFF.md` (operational handoff + restart runbook)
- `docs/PROJECT_STATUS.md` (achievements / gaps / priorities)
- `docs/NEXT_CHAT_PROMPT.md` (paste this into a new chat)
