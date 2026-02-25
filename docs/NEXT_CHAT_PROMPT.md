# New Chat Bootstrap Prompt (Paste into a New Codex Chat)

Use this when you start a new chat/session and want it to continue this project quickly.

---

I am continuing work on this RunPod project. Please read these files first before making changes:

- `docs/SESSION_HANDOFF.md`
- `docs/PROJECT_STATUS.md`

Important context:
- We are using RunPod and ports may change.
- `/workspace` is the persistent mount.
- Notification system is currently the main working feature and should not be broken.
- The app currently runs in dev with:
  - backend on port `8002`
  - frontend on port `5173`
- Frontend uses Vite proxy to reach backend.
- Full ML backend install is not complete because `/workspace` quota is too small.
- Temporary runtime tools may be used:
  - backend venv: `/tmp/demoSTT-api`
  - Node 22: `/tmp/node22`

Please:
1. Summarize what is already working from the handoff docs
2. Confirm which services are currently running
3. Continue from the notification system work unless I specify otherwise
4. Avoid overwriting `server/main.py` without checking current changes

If services are not running, use the restart steps in `docs/SESSION_HANDOFF.md`.

---

