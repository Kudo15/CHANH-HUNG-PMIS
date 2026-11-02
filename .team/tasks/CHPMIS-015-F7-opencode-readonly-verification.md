# CHPMIS-015-F7 — OpenCode Read-only Verification

## Role and authorization

- Role: independent read-only verifier.
- Task: review the F7 row-lock implementation and focused regression-test diff against the owner-approved proposal and current live verification evidence.
- Do not edit, stage, commit, or run mutating commands. Do not read environment values, credentials, or container configuration. Do not run tests; Coordinator has already run the assigned PostgreSQL checks with synthetic loopback context.

## Read scope

- `AGENTS.md`, `.team/CHARTER.md`, `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`, `.team/tasks/CHPMIS-015-F7-codex-worker.md`, `.team/tasks/CHPMIS-015-F7-reproduction-diagnosis.md`, `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`.
- Review only `backend/app/auth/routes.py` and `backend/tests/test_postgresql.py` for the F7 implementation, with emphasis on locking the existing target `User` row before the existing-role check and the two-distinct-requests PostgreSQL test contract. The files contain pre-existing unrelated changes from earlier tasks; preserve them and do not attribute or alter them as part of F7.

## Acceptance points

1. The target-row lock is in the same approval transaction and occurs before checking the existing canonical role.
2. Existing request-row lock, authorization checks, response behavior, audit fields, and session revocation remain intact.
3. The test uses an F7-specific synthetic database namespace, ensures competing requests reach the target-user lookup, and asserts one 200, one 409, one active canonical role, one approved plus one pending request, and target-session revocation.
4. No schema, migration, uniqueness constraint, broad workflow change, or out-of-scope file is introduced.
5. Consider whether the test synchronization can hang or conceal failure, and whether the new lock serializes different requests as intended.

## Evidence from Coordinator

- Focused PostgreSQL test: `1 passed, 5 deselected, 2 warnings in 2.69s`, exit 0.
- PostgreSQL module: `6 passed, 9 warnings in 5.01s`, exit 0.
- Full backend suite: `159 passed, 9 warnings in 12.46s`, exit 0.
- Ruff check, Ruff format check, and scoped `git diff --check`: all exit 0.

Return `APPROVED` or `CHANGES_REQUESTED`, with findings as `file:line`, priority, issue, and correction direction. Do not change implementation.
