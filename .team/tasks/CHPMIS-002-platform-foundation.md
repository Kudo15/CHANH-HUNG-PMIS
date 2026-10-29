# Task Pack — CHPMIS-002 Platform Foundation

## Task ID and execution role
- Task ID: CHPMIS-002
- Role: Worker (platform foundation)
- Status: READY TO DISPATCH; plan review confirmed; Docker runtime verification is known unavailable.

## Context
CHÁNH HƯNG PMIS is a new repository with approved product/architecture planning docs but no application files or dependencies. This task builds only the local technical foundation. It does not implement authentication, authorization policy, project/task schemas, business workflows, financial logic, or production deployment.

Fixed stack: React + TypeScript + Vite + Tailwind + shadcn/ui; FastAPI + SQLAlchemy 2 + Alembic + Pydantic; PostgreSQL; Docker Compose + CI; Pytest + Vitest + Playwright. Use Python 3.13 available through `py -3.13` unless dependency compatibility requires 3.12. Current tool check found Node 22.23.2/npm 10.9.8, Python 3.12/3.13 launchers, and no Docker executable.

## Objective
Create a runnable frontend/backend shell, PostgreSQL Compose service, migration framework with only a harmless empty baseline if needed, liveness/readiness checks, test scripts, and CI checks. Bind every published development port to `127.0.0.1`; use synthetic data only.

## Files in scope
- Create: `frontend/**`, `backend/**`, `compose.yaml`, `.github/workflows/ci.yml`.
- Modify only when needed: `README.md`, `.env.example`, `.gitignore`.
- Forbidden: business/auth/authorization schema or code, actual department/title/role seed values, product workflows, real data, secrets, production files, changes to product/architecture/security docs, Git remote/push/deploy/merge.

## Prompt templates retrieved from prompts.chat
1. **System Architect Agent Role**, ID `cmmx2hvgz0001ks04mcg6dizn`: https://prompts.chat/prompts/cmmx2hvgz0001ks04mcg6dizn_system-architect-agent-role
2. **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`: https://prompts.chat/prompts/cmmx34zl7000vil04rm2wl8yl_test-engineer-agent-role

### Modernized worker prompt
Act as a focused platform engineer for CHÁNH HƯNG PMIS. Analyze this bounded task and implement only the approved React/Vite and FastAPI/PostgreSQL local foundation. Preserve the mandated modular-monolith stack; do not introduce microservices, cloud infrastructure, product/auth/business schema, official department/role data, or external integrations. Work test-first: add a behavioral health/config test, observe its expected failure, implement the minimum, then run the real backend/frontend checks. Use synthetic fixtures and `.env.example` placeholders only. Ensure all Compose host bindings are loopback-only. Report exact changed files, commands, exit codes, TDD RED/GREEN evidence, and any `NOT_VERIFIED` results. Do not claim PASS for Docker checks because Docker is absent; mark them `NOT_VERIFIED` and do not install system Docker.

### Modernized tester guidance
Use the Test Engineer template's acceptance mapping, AAA structure, happy/error cases, focused-then-full tests, deterministic fixtures, and actual output reporting. Ignore its generic 80% coverage/mutation thresholds, microservice/contract-testing assumptions, and any suggestion to create unrelated TODO files; this task has no approved numeric coverage target and is a modular monolith.

## Acceptance criteria
- [ ] React + TypeScript + Vite frontend shell builds and has a runnable Vitest command.
- [ ] FastAPI backend starts and has `/health/live` and `/health/ready`; readiness accurately reflects PostgreSQL dependency availability.
- [ ] SQLAlchemy 2 and Alembic are configured; any initial revision contains no business/auth tables or seed data.
- [ ] Compose defines frontend/backend/PostgreSQL as needed; every host-published port is bound to `127.0.0.1`; no external service or production profile.
- [ ] CI runs backend/frontend checks and tests without a deploy job or secrets.
- [ ] `.env.example` contains placeholders only; `.gitignore` excludes `.env`, venvs, node_modules, generated artifacts, and local DB data.
- [ ] Focused tests and available builds pass with exact commands/exit codes. Docker execution/config validation may be `NOT_VERIFIED` because Docker is not installed.

## Verification commands
- `py -3.13 -m pytest -q` from `backend/` (or document an equivalent exact script and its exit code).
- `npm test -- --run` and `npm run build` from `frontend/`.
- `docker compose config` and startup/readiness checks if Docker becomes available; otherwise report `NOT_VERIFIED` with observed missing executable.

## Traceability
Mission §§2, 6, 7C; `ARCHITECTURE.md`; plan Task 1; AC-01–AC-04 and AC-15.

## Risks and Human Gates
No business/auth schema or security policy is approved yet. Keep this scaffold free of those choices. Docker runtime tests cannot run in the current host. Do not install Docker or configure production.

## Report format
Files changed; tests/commands with exit codes; TDD RED/GREEN evidence; review concerns; `BLOCKED`/`NOT_VERIFIED` items; commit hash if created.

## Definition of Done
- All safe local checks run and are reported honestly.
- Compose locality and secret boundaries are inspected.
- Task reviewer finds no spec violation; any Docker runtime/config gap remains explicitly `NOT_VERIFIED`.
- `.team/ledger.md` records the outcome; no later auth/schema task is implied complete.
