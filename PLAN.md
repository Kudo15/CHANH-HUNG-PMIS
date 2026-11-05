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
Status as of 2026-11-03: HG1–HG5 are approved for the local first slice. CHPMIS-017 is complete for its local authorization scope. CHPMIS-012-F1 implementation and independent review are complete, but its PostgreSQL module skipped all six live checks; CHPMIS-012-F2 local Keycloak configuration is complete, but live Keycloak/browser login is not verified. CHPMIS-011 remains in progress. CHPMIS-019-F1 is complete with the owner's scoped diff-check substitution and fresh OpenCode evidence review; its original verifier session-start gap remains recorded. CHPMIS-020 implementation is approved but remains in progress with partial independent backend evidence and no remote CI. CHPMIS-018-F1's Worker reported a live synthetic PostgreSQL lost update; its T1 remains blocked, so live RED remains NOT_VERIFIED independently. CHPMIS-018-F2 is complete with the owner's scoped acceptance of the Coordinator's six final checks and independent R2 review; all six OpenCode Tester checks remain NOT_VERIFIED and the nonblocking P3s/process deviation remain recorded.

The current Alembic head is `0007_oidc_pkce_browser_binding`. CHPMIS-021 ran an empty-database upgrade to 0007 and inspected its 12 tables; a fresh OpenCode Reviewer read the required session documents and approved the evidence. AC-03 is PASS. Current acceptance is **12 PASS / 0 PARTIAL / 3 NOT_VERIFIED**; AC-04 remote CI, AC-05 synthetic-provider sign-in and AC-14 authenticated browser E2E are NOT_VERIFIED. CHPMIS-012-F1's full PostgreSQL module remains independently unverified.

CHPMIS-009 remains a historical checkpoint, not a stage/commit. Its manifest is not a current acceptance audit and must not be regenerated to conceal later source/docs changes. The checkout remains dirty; no remote, push, deployment, or merge is authorized.
## Next execution order
Execute the owner's selected order against the existing dirty checkout and preserve prior work:
1. COMPLETE — CHPMIS-021 ran a separate synthetic PostgreSQL upgrade from empty through `0007_oidc_pkce_browser_binding`; fresh independent OpenCode evidence review is approved.
2. CHPMIS-019-F1 COMPLETE: owner accepted the Coordinator's exact scoped diff check as substitution for OpenCode's denied command; fresh CHPMIS-022 Reviewer approved the narrow evidence and recorded the original verifier session-start gap. CHPMIS-020: OpenCode independently passed 45 bootstrap tests before a Ruff denial; the Coordinator passed the full local suite with PostgreSQL skips and Ruff. Remote Windows CI remains unobserved.
3. COMPLETE — CHPMIS-018-F2 closed with the owner's scoped evidence substitution and R2 APPROVED review; its OpenCode Tester checks remain NOT_VERIFIED. Keep CHPMIS-018-F1 T1 blocked under the existing owner decision; live RED remains NOT_VERIFIED independently. See `.team/tasks/CHPMIS-018-F2-task-transition-worker.md` and `.team/ledger.md`.
4. IN PROGRESS — the staged local synthetic Keycloak/bootstrap and mixed UI/API E2E candidate for AC-05/14 has independent OpenCode approval for further planning, with missing executable assets and prerequisites recorded. Implement and independently review bounded supporting assets, then consolidate the exact procedure for a separate owner Human Gate. The existing runbook says DO NOT EXECUTE; no host Registry/account/ACL changes or live bootstrap are authorized. See `.team/tasks/CHPMIS-011-runtime-approval-proposal.md`.
5. Keep README, PLAN, TASKS, ACCEPTANCE, and ledger synchronized with accepted evidence; retain historical snapshots and preserve unanswered date/timezone and auth-state policy questions.
6. Leave remote CI NOT_VERIFIED: there is no Git remote, and this plan prohibits creating one or pushing. A later owner decision and an actual candidate-revision run are needed for that gate.

The audit gate is recomputed on the exact final SHA. The multi-department slice stays blocked until in-scope P1/P2 findings are closed, required PostgreSQL and browser E2E checks pass without skips, remote CI passes that SHA, and independent review is accepted. Preserve existing `chpmis010` resources. No actual organization IdP, production identity, registry/account/ACL mutation, deployment or production use is authorized by this plan.

After first-slice gates: scope M15 administration, M05 documents and M06 notifications. Provider, document classification/retention and any new permission/workflow decisions require their own approval.

No real IdP connection, production retention policy, S3 provider, deployment or official legal/financial rule is approved by this roadmap. See `OPEN_QUESTIONS.md` and `.team/baselines/CHPMIS-009-checkpoint.md`.
