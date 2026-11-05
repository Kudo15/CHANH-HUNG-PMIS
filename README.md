# CHÁNH HƯNG PMIS

Secure modular-monolith project information management system for Ban QLDA phường Chánh Hưng.

## Current stage

As of 2026-11-03, the local first slice includes the OIDC/session and authorization foundation, project/task workflow, dashboard/audit, Project Workbench, and the scoped CHPMIS-012-F1 PKCE/browser-binding implementation. CHPMIS-019-F1 is complete with the owner's approved substitution for a denied OpenCode diff check; its earlier verifier session-start gap remains recorded. CHPMIS-020 is in progress. CHPMIS-018-F1's Worker reports a live synthetic PostgreSQL lost update; the independent Tester was blocked by its shell allowlist, so live RED remains NOT_VERIFIED independently. The owner chose to keep F1-T1 blocked and accepted the Coordinator's six final checks plus independent R2 review as a scoped substitute to close CHPMIS-018-F2; the six OpenCode Tester checks remain NOT_VERIFIED. Acceptance records 12 PASS and 3 NOT_VERIFIED: CHPMIS-021 ran the empty-database migration through current head `0007_oidc_pkce_browser_binding` and a fresh OpenCode Reviewer approved the evidence. AC-04 remote CI, AC-05 live synthetic-provider sign-in, and AC-14 authenticated browser E2E remain NOT_VERIFIED. See `ACCEPTANCE.md` for the evidence and `.team/ledger.md` for task status.

CHPMIS-009 completed documentation reconciliation and candidate checkpoint preparation, with OpenCode independent verification and Hermes review approval. Its manifest is a historical snapshot; subsequent source commits and the current uncommitted changes are reflected in Git status. See `.team/baselines/CHPMIS-009-checkpoint.md`.

## Start here

1. Read `AGENTS.md` and `.team/CHARTER.md`.
2. Review `docs/MISSION.md`, `docs/product/PRD.md`, and `OPEN_QUESTIONS.md`.
3. Review the first vertical slice plan at `docs/superpowers/plans/2026-10-29-chanh-hung-pmis-vertical-slice.md`.
4. Read current status and execution order in `PLAN.md` and `TASKS.md`. HG1–HG5 are approved for the local first slice; production/provider/bootstrap decisions remain open in `OPEN_QUESTIONS.md`.

## Project documents

- Mission and PRD: `docs/MISSION.md`, `docs/product/PRD.md`
- Roles and stories: `docs/product/USER_ROLES.md`, `docs/product/USER_STORIES.md`
- Architecture/API/data: `docs/architecture/`
- Workflow and security: `docs/workflows/`, `docs/security/`
- Legal register: `docs/legal/LEGAL_RULES_REGISTER.md`
- Acceptance/tasks/open questions: `ACCEPTANCE.md`, `TASKS.md`, `OPEN_QUESTIONS.md`

## Tooling status

- Superpowers exists in the current Codex skill catalog.
- Prompt-search skill `prompt-lookup` is installed in `.agents/skills/prompt-lookup`; Codex is connected to `https://prompts.chat/api/mcp`. Search and retrieval were verified for architecture, code review, and testing templates; adapted template IDs and links are recorded in the Worker task pack.
- Environment observations from CHPMIS-002/006: Node 22.23.2/npm 10.9.8 and Python 3.12/3.13 were available; Docker was absent. CHPMIS-009 does not recheck or install runtime tools; CHPMIS-010 subsequently completed runtime preflight and verification.
- CHPMIS-010 update: owner-authorized Docker Desktop 4.97.0 installed per-user with verified published SHA/signature. CLI 29.9.2 and Compose v5.6.1 work; Compose configuration validation exit 0. Owner handled terms; Engine/stack/PostgreSQL verification completed, focused test 1 passed/full 63 passed, Hermes evidence review APPROVED. Task containers are stopped and synthetic volume retained. In older shells use `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe` if PATH has not refreshed.
- Routing in `.team/routing.json`: Hermes CLI Kanban Worker and separate Reviewer on the inherited `default` profile; independent OpenCode `role-verifier` Tester on its configured default model; Codex Coordinator/Planner on its configured default. Run sequentially in the existing checkout until a committed baseline is verified in any worktree. Dispatch is explicit.
- Git is local with no remote. CHPMIS-009 prepares, but does not stage or commit, the checkpoint candidates.

## Run the local foundation

Requires Node 22.23.2+, Python 3.13, and Docker Compose v2 for the full stack.

1. Copy `.env.example` to `.env`. Replace the password placeholder in both `POSTGRES_PASSWORD` and `DATABASE_URL` with the same synthetic development value. URL-encode password characters in the URL.
2. From the repository root, run `docker compose up --build -d`.
3. Apply the current migration head, `0007_oidc_pkce_browser_binding`: `docker compose exec backend python -m alembic upgrade head` against a disposable synthetic development database. The command targets the current head; a live empty-database upgrade through 0007 is still NOT_VERIFIED.
4. Open `http://127.0.0.1:5173`. API health is at `http://127.0.0.1:8000/health/live` and `/health/ready`.
5. Stop with `docker compose down`. The named PostgreSQL volume persists local data.

Every published Compose port binds to `127.0.0.1`. Container processes listen on their container interfaces so the loopback mappings can reach them. This configuration is for local synthetic development.

### Native backend (PowerShell)

```powershell
cd backend
py -3.13 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
$env:DATABASE_URL = 'postgresql+psycopg://pmis_dev:CHANGE_ME_LOCAL_ONLY@127.0.0.1:5432/pmis_dev'
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set `DATABASE_URL` in the process environment; the backend does not load a `.env` file automatically. An unset database URL allows liveness to run and returns readiness HTTP 503. Readiness runs `SELECT 1` on each request and returns HTTP 200 only when the dependency responds. It does not certify migration currency. Database connection and statement timeouts are three seconds each.

### Frontend and verification

From `frontend/`: `npm ci`, `npm run dev`, `npm test -- --run`, `npm run lint`, and `npm run build`. The development server binds to `127.0.0.1:5173` and proxies `/api` and `/health` to the configured backend. Full browser API/OIDC routing is not yet verified. Run `npx playwright install chromium` once, then `npm run test:e2e` for the shell smoke check; it is not the complete authenticated journey.

From `backend/`: `.venv/Scripts/python -m pytest -q`, `.venv/Scripts/python -m ruff check .`, and `.venv/Scripts/python -m ruff format --check .`. On Linux/CI use `python` from the installed environment. `python -m alembic upgrade head --sql` renders the migration chain offline; it does not verify PostgreSQL execution. PostgreSQL integration tests skip without `TEST_DATABASE_URL`. CHPMIS-021 ran the focused empty-database test on a dedicated synthetic service and inspected revision 0007 and 12 tables; a fresh OpenCode Reviewer approved the evidence without a runtime rerun. The CHPMIS-012-F1 full PostgreSQL module remains independently unverified. Use only a dedicated synthetic test database.

CI defines backend lint/tests with disposable PostgreSQL, Compose config validation, frontend lint/tests/build, and a Playwright shell smoke check. No remote CI run or Docker runtime/config result is implied by adding this workflow.
