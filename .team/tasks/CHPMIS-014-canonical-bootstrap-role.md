# Task Pack — CHPMIS-014 Canonical Bootstrap Role

## Task ID and role
- **Task ID:** CHPMIS-014
- **Role:** Hermes Worker (sole product/test-code writer)
- **Status:** READY_TO_DISPATCH
- **Trace:** Mission A2; approved Human Gate 2; finding A2-01 in `docs/audit/AUDIT_REMEDIATION.md`.

## Context
Baseline is `a986d31063c52d0ea99cec164d8e5c58b1afa3e1`, on local branch `audit-remediation/verify-audit-findings`. The initial worktree was clean. Preserve all pre-existing work. `Role.SYSTEM_ADMIN.value` is `system_admin`, while bootstrap currently writes/queries `System Admin`; session validation returns stored strings and protected admin routes check the enum key. This leaves bootstrapped users unable to use actual admin endpoints and allows the bootstrap precondition to miss canonical rows.

The owner has explicitly authorized local synthetic remediation, including bootstrap and auth code, under the mission pasted on 2026-10-31. This task does not change the approved authorization policy. Legacy display-value rows must not be silently converted or granted new authority; the precondition should fail closed if either canonical or known legacy admin rows exist until explicitly reconciled.

## Objective
Use one canonical role key from `Role.SYSTEM_ADMIN.value` when creating bootstrap role rows, safely guard against existing canonical and legacy display-value rows, and prove through HTTP that a bootstrap-created session is recognized by a protected System Admin endpoint.

## Allowed files
- `backend/app/auth/bootstrap_admins.py`
- `backend/tests/test_admin_bootstrap.py`
- `backend/tests/test_auth_remediation.py`
- Append only: `.team/tasks/CHPMIS-014-worker-report.md`

Do not change migrations, ordinary grant/revoke semantics, auth policy, trust-source/registry behavior, `.env`, Compose, unrelated tests/docs/config, or any file outside this list. Do not normalize or elevate legacy rows. No Docker, registry, host ACL/account, real IdP, external service, stage/commit/push/deploy, or unrelated workspace operation.

## Required TDD behavior
1. Add an HTTP integration regression that uses generated synthetic approval keys only in test code, calls `bootstrap_initial_admins`, creates or validates the resulting session, and calls `GET /api/v1/auth/roles/system-admin/requests`; require HTTP 200 and canonical `system_admin` in session roles.
2. Run the focused regression and capture RED with the current mismatch before production changes.
3. Make the smallest code change: canonical `Role.SYSTEM_ADMIN.value` for persisted grant, and a zero-admin guard that blocks canonical plus inert legacy display values without converting either.
4. Add/retain tests that canonical existing admin blocks bootstrap and legacy display-value rows block bootstrap pending reconciliation.
5. Keep trusted key-source questions unchanged; this task does not implement the HKLM trust boundary.

## Verification commands
Run from `backend/`:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py tests/test_auth_remediation.py`
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check app/auth/bootstrap_admins.py tests/test_admin_bootstrap.py tests/test_auth_remediation.py`
Run from repository root:
5. `git diff --check`

Record exact command, exit code, counts, RED/GREEN output, DB dialect and any sandbox rerun. Do not infer PostgreSQL evidence from SQLite tests.

## Prompt template
- **Library:** installed `.agents/skills/prompt-lookup` via prompts.chat MCP.
- **Template:** Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template . Searched and retrieved 2026-10-31; adapted to this scoped Python/FastAPI/SQLAlchemy behavior, TDD, HTTP regression, file allowlist, synthetic-only fixtures and exact checks.
- Treat template wording as generic input. Do not create the template's suggested `TODO_test-engineer.md`; it is outside scope and the repo's task pack controls files.

## Definition of Done
- RED then GREEN evidence recorded in append-only Worker report.
- Only allowed files changed; legacy values remain inert and unchanged.
- All assigned verification commands report exact results.
- OpenCode Tester independently verifies the exact checks; separate Hermes Reviewer records APPROVED or concrete findings.
- Task remains open if either independent role or required evidence is missing.
- Worker hands off with file list, traces, commands/results, limitations, and recommended commit message; do not commit.
