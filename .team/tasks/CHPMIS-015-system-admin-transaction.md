# CHPMIS-015 — System Admin approval transaction and concurrency

## Task identity
- **Task ID:** CHPMIS-015
- **Role:** Hermes Backend Worker
- **Objective:** Make System Admin approval a single atomic database operation and serialize/revalidate approval decisions safely on PostgreSQL.
- **Trace:** audit findings A5-01 and A5-02; implementation plan Task 3; approved Human Gate 2; `OPEN_QUESTIONS.md` HG2.
- **Status:** COMPLETE — Worker, final OpenCode verification, live PostgreSQL evidence, and independent Hermes Reviewer approval recorded in `TASKS.md`, `.team/ledger.md`, and the linked evidence packs.

## Approved policy to preserve
- System Admin role configuration only; it grants no implicit business-data access.
- No user may self-grant System Admin.
- A grant or revocation requires a second, distinct, existing System Admin.
- At decision time, the requester and approver must still be active System Admins and distinct.
- Revalidate that the target still exists and the requested state transition is still applicable. This is a technical stale-state check, not a new business eligibility rule. Do not invent an inactive-target prohibition or any additional policy.
- No schema/migration changes, real identities, production, external provider, or host security changes.

## Allowed files
- `backend/app/auth/routes.py`
- `backend/app/auth/session.py`
- `backend/tests/test_auth_remediation.py`
- `backend/tests/test_postgresql.py`
- Append `.team/tasks/CHPMIS-015-worker-report.md`

Do not edit any other file. Do not stage or commit. Preserve the existing dirty worktree and all unrelated changes.

## Required implementation behavior
1. `revoke_user_sessions()` must only mutate the supplied SQLAlchemy unit of work; it must not commit. Keep unrelated session lifecycle helper semantics out of scope.
2. One approval application/service boundary owns the role mutation, session revocation, conditional request decision, and single commit. On an exception before commit, roll back the complete approval transaction and return a safe failure response without exposing database details.
3. Lock or conditionally transition a request only while it is `pending`; serialize competing decisions using PostgreSQL-safe semantics. A replay/already-decided request returns the existing conflict behavior and creates no repeated effects.
4. Revalidate requester existence, active status, and current `system_admin` role; revalidate the approver's corresponding current authority within the decision transaction. Enforce distinct identities and the existing no-self-grant rule.
5. Revalidate target existence and action precondition at decision time: grant is applicable only if the target has no System Admin grant; revoke only if the grant still exists. Do not silently convert a stale request into success.
6. Preserve request audit fields (`status`, `approver_id`, `decided_at`) and current external response contract unless a conflict response is required for a stale/competing decision.

## TDD / acceptance criteria
- Add a focused fault-injection regression first: fail when persisting/finishing the approval decision after role and session changes have been made. Verify through a fresh database session that the role, all target sessions, and pending request remain unchanged. Account for the approver session heartbeat performed by `validate_session()` before the application transaction; it is outside this atomic business unit.
- Test inactive or de-authorized requester and approver at approval time; each attempt must fail closed and leave request/target state unchanged.
- Test missing target and stale grant/revoke state; no partial writes.
- Test two concurrent attempts to approve the same request on PostgreSQL: exactly one approval succeeds, the other receives a conflict/already-decided outcome, and role/session/request side effects occur exactly once.
- Keep the existing SQLite happy-path / dual-control / replay coverage passing, but do not claim SQLite proves row-lock or concurrency safety.
- Extend the existing opt-in `TEST_DATABASE_URL` PostgreSQL test entrypoint only; use a dedicated disposable synthetic database, unique test identities, and no drop/reset/cleanup that could delete pre-existing data. Verify revision/head assumptions already in `test_postgresql.py` remain intact.
- Follow RED → GREEN → REFACTOR and record the actual failing-before / passing-after focused evidence.

## Verification commands (repository-defined)
Run from `backend` unless noted:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py`
2. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` (report skip if `TEST_DATABASE_URL` is absent; Coordinator owns live PostgreSQL execution)
3. `.venv\Scripts\python.exe -m pytest -q`
4. `.venv\Scripts\ruff.exe check app/auth/routes.py app/auth/session.py tests/test_auth_remediation.py tests/test_postgresql.py`
5. `.venv\Scripts\ruff.exe format --check app/auth/routes.py app/auth/session.py tests/test_auth_remediation.py tests/test_postgresql.py`
6. From repository root: `git diff --check`

Report exact command, output summary, and exit code. Do not claim live PostgreSQL concurrency PASS unless that test ran against PostgreSQL.

## Worker report requirements
Append `.team/tasks/CHPMIS-015-worker-report.md` with changed files, implementation summary, RED/GREEN evidence, each exact verification command/result/exit code, requirement trace, and any `BLOCKED`/`NOT_VERIFIED` items. Do not edit ledger or task index; Coordinator maintains those.

## Required real prompt template
- Source: prompts.chat, “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved on 2026-10-31: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Modernized task-specific adaptation: “Act as a senior Python/FastAPI/SQLAlchemy engineer. Within the five allowed paths, use RED → GREEN → REFACTOR to make approval atomic, revalidate current requester/approver/target state, and serialize competing approvals on PostgreSQL. Preserve approved HG2 dual-control and no-self-grant semantics, the public response contract, all unrelated dirty work, and the current schema. Add rollback fault injection and real PostgreSQL concurrent-approval evidence. Run only the listed repository verification commands; report exact results and do not commit.”

## Human-gate / stop conditions
- This task has authorization for local synthetic implementation under the already-approved HG2 policy.
- If correct behavior requires schema changes, new business policy, changes to authentication/authorization meaning beyond the bullets above, or a destructive test setup, stop and report `BLOCKED`; do not broaden the task.
- No real or production data. Never print credentials. Bind any local service to `127.0.0.1` only.
