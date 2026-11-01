# CHPMIS-015-F2 — Keep PostgreSQL fixture identity after session close

- **Task ID:** CHPMIS-015-F2
- **Role:** Hermes Backend Worker
- **Parent:** CHPMIS-015, concurrency fixture follow-up
- **Trace:** A5-01/A5-02 PostgreSQL concurrent-approval acceptance; `.team/tasks/CHPMIS-015-system-admin-transaction.md`
- **Status:** READY_FOR_WORKER

## Exact evidence
After CHPMIS-015-F1 repaired the `granted_by` foreign key, Coordinator reran the live PostgreSQL command on `chpmis015_test`. The test observed exactly one HTTP 200 and one HTTP 409 with “already decided”; then it exited 1 at the postcondition query with SQLAlchemy `DetachedInstanceError` because it dereferenced `target_user.id` after the fixture session closed. Full run: `1 failed, 1 passed`, exit 1. The test has not passed yet.

## Scope
- Allowed implementation file: `backend/tests/test_postgresql.py` only.
- Append a short section to `.team/tasks/CHPMIS-015-worker-report.md` describing this fixture correction; preserve previous sections.
- No production code, schema/migrations, environment files, task index/ledger, unrelated tests, database deletion/reset, or resource removal. Use synthetic data only; Coordinator owns live DB rerun.

## Required correction
Capture the synthetic target ID (and any other ORM IDs needed after the `with DBSession(...)` block) into plain string variables while the session is open. Use only those captured values in post-session assertions. Keep the HTTP assertions exactly one `200` plus one `409` and the postconditions for one role, revoked target session, and one approved request. Do not weaken assertions or change the concurrent request behavior.

## Verification
- Coordinator's failing live PostgreSQL run is the RED evidence; preserve the same test database.
- Worker may run only `.venv\Scripts\ruff.exe check tests/test_postgresql.py`, `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py`, and root `git diff --check -- backend/tests/test_postgresql.py .team/tasks/CHPMIS-015-worker-report.md`.
- Coordinator will run the focused PostgreSQL tests on the dedicated `chpmis015_test` database after the fix. Do not claim live concurrency PASS.
- Report exact output and exit code for every command.

## Required real prompt template
- prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved via installed prompt-lookup on 2026-10-31: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Task adaptation: “Act as a senior Python/PostgreSQL test engineer. In only `backend/tests/test_postgresql.py`, capture required synthetic ORM IDs before the SQLAlchemy session closes and use the plain IDs in later assertions. Preserve the exact one-200/one-409 concurrency assertions and all state postconditions. Do not alter production code or data; run only the listed lint/format/diff checks, append evidence, and do not commit.”

## Stop conditions
If any fix requires a schema, policy, or production-code change, or database reset/deletion, stop and report `BLOCKED`.
