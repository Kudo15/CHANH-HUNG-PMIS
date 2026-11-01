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
1. Confirm identity source/session mechanism; configurable department/role/scope model; first-slice project fields; task states/transitions; audit fields/access/retention. **Approved for local first slice on 2026-10-30**; production/legal/provider items remain separately gated in `OPEN_QUESTIONS.md`.
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
HG1–HG5 are approved for the local first slice. CHPMIS-003/F1 and 004–010 completed their scoped local deliverables. CHPMIS-002 remains PARTIAL only for remote CI evidence. CHPMIS-010 closed AC-01/03: actual Compose/PostgreSQL migration/health/loopback checks, focused 1 passed and backend 63 passed/no skips, exit 0; Hermes Reviewer accepted recorded Coordinator runtime evidence (no independent live rerun). Acceptance is **12 PASS / 3 NOT_VERIFIED**: AC-04 remote CI, AC-05 actual IdP sign-in, AC-14 authenticated E2E.

OpenCode independent CHPMIS-010-T1 regression predates runtime setup: 62 passed/1 skipped, exit 0. Frontend evidence remains CHPMIS-007: 15 tests, lint/build and one Playwright shell check. These do not prove actual IdP/browser flow. First Hermes runtime Reviewer was blocked/stopped after a safety deviation; clean evidence-only review t_a11e6713/run 32 APPROVED, zero P1/P2/P3. Details and skill/run trace in `.team/tasks/CHPMIS-010-runtime-evidence.md`.

CHPMIS-009 prepared a historical checkpoint, not a stage/commit. Its manifest must not be regenerated to conceal CHPMIS-010 source/docs changes; audit-baseline.mjs checks its original task-specific counts and is not a current acceptance audit. Dirty source still requires a separately authorized verified local checkpoint before worktree isolation. No remote/push/deploy occurred.

CHPMIS-017 is complete for local scope: F1 and F2 received independent review, the final Worker backend suite reported 138 passed and 2 skipped, and scoped Ruff/format on seven files passed. OpenCode process deviations remain recorded; 14 historical out-of-scope Ruff findings are tracked as CHPMIS-017-L1. The next planned item is CHPMIS-012, whose scoped implementation/runtime task pack has not yet been prepared; its authentication and external-provider gates remain applicable.
## Next execution order
The 2026-10-31 audit mission adds confirmed defects to the earlier roadmap. Preserve CHPMIS-012 (browser OIDC/authenticated E2E) and CHPMIS-013 (schema/CI) as previously reserved IDs; do not reuse them. Continue sequentially on the audit branch with the bounded task packs and synthetic local evidence:
1. **CHPMIS-014** — canonical System Admin bootstrap role and protected HTTP regression (`.team/tasks/CHPMIS-014-canonical-bootstrap-role.md`).
2. **CHPMIS-013** — schema/migration/CI contract, including live PostgreSQL upgrade and downgrade evidence.
3. **CHPMIS-015** — System Admin approval atomicity, authority revalidation, and PostgreSQL concurrency.
4. **CHPMIS-016** — approved local synthetic bootstrap trust-source behavior; real registry provisioning, identities and custody stay gated.
5. **CHPMIS-017** — HTTP authorization matrix across roles, endpoints and scopes.
6. **CHPMIS-012** — browser OIDC fixes followed by authenticated synthetic Playwright E2E through frontend, backend, PostgreSQL and Keycloak.
7. **CHPMIS-018** — PostgreSQL task concurrency and project/member consistency.
8. **CHPMIS-019** — frontend structured errors, stale response/session state and calendar-date correctness.

The audit gate is recomputed on the exact final SHA. The multi-department slice stays blocked until in-scope P1/P2 findings are closed, required PostgreSQL and browser E2E checks pass without skips, remote CI passes that SHA, and independent review is accepted. Preserve existing `chpmis010` resources. No actual organization IdP, production identity, registry/account/ACL mutation, deployment or production use is authorized by this plan.

After first-slice gates: scope M15 administration, M05 documents and M06 notifications. Provider, document classification/retention and any new permission/workflow decisions require their own approval.

No real IdP connection, production retention policy, S3 provider, deployment or official legal/financial rule is approved by this roadmap. See `OPEN_QUESTIONS.md` and `.team/baselines/CHPMIS-009-checkpoint.md`.
