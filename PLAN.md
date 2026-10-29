# CHÁNH HƯNG PMIS — Delivery Plan

## Goal
Deliver a secure, locally runnable first vertical slice for authorized users: sign in → create project → assign staff → assign/update task → view scoped dashboard → inspect audit history.

## Fixed constraints
- Modular monolith and mandated React/TypeScript/Vite/Tailwind/shadcn/ui, FastAPI/SQLAlchemy 2/Alembic/Pydantic, PostgreSQL, S3-compatible storage, Docker Compose, CI, Pytest/Vitest/Playwright.
- MVP scope M01–M06 and M15. Do not start deferred modules before platform/security gate.
- Synthetic development data only; localhost-only service bindings; no secrets or agency records in Git.
- No production deployment. No legal/financial rule inference or sensitive external LLM use.
- Human Gate before risky schema, authorization, financial, approval-workflow, provider, or deployment changes.

## Phase 0 — Discovery and Human Gates
1. Confirm identity source/session mechanism; configurable department/role/scope model; first-slice project fields; task states/transitions; audit fields/access/retention.
2. Security reviewer validates a threat model and authorization matrix proposal.
3. Reviewer approves the detailed plan and each gated design before schema/auth/workflow implementation.

## Phase 1 — Foundation
1. Create monorepo layout for `frontend/` and `backend/`; pin supported dependency versions after environment discovery.
2. Add local Docker Compose for web, API, PostgreSQL; bind published ports only to `127.0.0.1`; use synthetic fixtures and `.env.example` only.
3. Add backend liveness/readiness checks, frontend shell, migrations, and test/lint commands.
4. Add CI for backend, frontend, migration/config validation, and browser checks without secrets or deployment steps.

## Phase 2 — First Vertical Slice
1. Implement approved authentication and server-side authorization.
2. Implement project create/read/list and staff assignment under approved scope rules.
3. Implement task create/assign/status transitions under approved workflow rules.
4. Implement scoped dashboard summary and audit-history read path.
5. Add unit, integration, authorization-negative, and E2E coverage for the acceptance matrix.

## Phase 3 — Independent Verification
1. Tester runs the project verification commands and records exact exit codes/evidence.
2. Independent reviewer reviews specification compliance first, then quality/safety.
3. Security review checks identity, cross-project/department isolation, workflow enforcement, and audit coverage.
4. Record unresolved criteria as `NOT_VERIFIED`; do not claim PASS without evidence.

## Execution state
Phase 0 documentation is prepared. Implementation is not started because prompt-template lookup is unavailable and Human Gate decisions for identity, schema, authorization, workflow, and audit policy are unresolved. See `OPEN_QUESTIONS.md`, `TASKS.md`, and `docs/superpowers/plans/2026-10-29-chanh-hung-pmis-vertical-slice.md`.
