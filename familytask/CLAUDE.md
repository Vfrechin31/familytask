# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FamilyTask is a learning project (built incrementally, day by day, per the French-language commit messages like "Jour 1"). The README explicitly states the repo starts as a near-empty skeleton that gets filled in over time — don't assume missing functionality is a bug; check whether it simply hasn't been built yet.

A finished reference implementation exists at `../corrections/step-8-final` (outside this repo) — it's there to check against, not to copy from.

## Running the app

Everything runs via Docker Compose (three services: `frontend`, `backend`, `db`):

```bash
docker compose up
```

- Frontend (Vite dev server, hot reload): http://localhost:5173, proxies `/api/*` to the backend container.
- Backend (FastAPI, `--reload`): http://localhost:8000, Swagger UI at `/docs`.
- DB: Postgres 16, credentials `familytask`/`familytask`, persisted in the `pgdata` volume.

In GitHub Codespaces, `CODESPACES` env var is forwarded to the frontend container so `vite.config.js` can adjust `allowedHosts` and HMR client port for the `*.app.github.dev` proxy domain.

There is no test suite and no linter configured in either project.

### Running services individually (without Docker)

- Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload` — defaults to a local SQLite file (`familytask.db`) when `DATABASE_URL` is unset.
- Frontend: `cd frontend && npm install && npm run dev` (also `npm run build`, `npm run preview`).

### End of a work session

The README's stated workflow (aimed at the learner) is: commit, push, then `docker compose down` and stop the Codespace.

## Architecture

### Backend (`backend/main.py`)

Single-file FastAPI app using SQLModel (SQLAlchemy + Pydantic). No routers/modules split — everything (models, auth, routes) lives in this one file.

- **Auth**: custom bearer-token scheme, not JWT. `POST /api/signup` and `POST /api/login` issue a random `secrets.token_hex(32)` stored directly on the `Member` row (`Member.token`). Every other endpoint depends on `get_current_member`, which looks up the member by exact token match via `HTTPBearer`. Logout just nulls the token server-side. Passwords are SHA-256 hashed (`hash_password`) — not salted/bcrypt, worth flagging if this project moves toward production use.
- **Multi-tenancy model**: there's no `Family` table. A `family_code` (random 6-char hex, generated at signup) is stamped onto both `Member` and `Task` rows and used to scope queries. The first member to sign up for a `family_code` becomes `is_admin=True`; there is currently no endpoint to join an existing family with an existing code (signup always creates a new family).
- **Authorization pattern**: admin-only routes check `current_member.is_admin` inline (e.g. `list_family_tasks`, and the "assign task to someone else" branch in `create_task`) rather than via a dependency/decorator.
- **Route ordering matters**: `/api/tasks/famille` is declared before `/api/tasks/{task_id}` specifically to avoid the path param swallowing the literal segment — keep that ordering if adding more static sub-paths under `/api/tasks`.
- Some task routes (`get_task`, `update_task`, `delete_task`, `toggle_task`) do **not** currently check `current_member`/family ownership before acting — only `list_tasks`/`list_family_tasks`/`create_task` scope by member or family. Be aware of this when extending those routes.
- `docker-compose.yml` wires an `AI_TOKEN` env var (intended for calling GitHub Models for an AI assistant feature) through to the backend container, but `main.py` has no AI-related routes yet — this is a planned/future feature, not currently wired up.

### Frontend (`frontend/src/`)

Vue 3 + Vite, no state management library (component-local `ref`/`computed` only), Vue Router for navigation.

- **`api.js`**: single `apiFetch(endpoint, options)` helper — prefixes `/api`, injects `Authorization: Bearer <token>` from `localStorage.getItem('token')` when present. All API calls should go through this, not raw `fetch`.
- **`router/index.js`**: routes are `/signup`, `/login`, `/tasks` (guarded by `meta: { requiresAuth: true }`), and `/` → redirect to `/tasks`. The nav guard checks only for token *presence* in `localStorage`, not validity — an expired/invalid token still passes the guard and fails later at the API call.
- **`App.vue`**: shell that renders a top bar (name + logout) when a member is loaded via `/api/me`, plus `<router-view>`. Re-fetches `/api/me` on every route change.
- **`views/TasksView.vue`**: currently contains a **local hardcoded mock user-switcher** (`users` ref with 4 fixed names/roles and a `switchUser` picker) layered on top of real API calls to `/api/tasks` and `/api/members`. This mock selection UI is not wired to the real `/api/login` auth flow (`Login.vue`/`Signup.vue`/token-based `currentMember`) — treat this as in-progress/scaffolding rather than the intended final UX, and check with the user before assuming which system (mock switcher vs. real auth) should be extended.
- Task "done-by" stats in `TasksView.vue` are purely client-side (`stats` ref, incremented in `toggleTask`) — the backend has no field tracking who completed a task, so this resets on reload/is not persisted.
