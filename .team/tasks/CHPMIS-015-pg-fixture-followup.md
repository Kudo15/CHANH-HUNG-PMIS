# CHPMIS-015-F1 — Repair PostgreSQL concurrency fixture

- **Task ID:** CHPMIS-015-F1
- **Role:** Hermes Backend Worker
- **Parent:** CHPMIS-015, Worker card `t_47da9e47` / run #66
- **Trace:** A5-01, A5-02, HG2; parent pack `.team/tasks/CHPMIS-015-system-admin-transaction.md`
- **Status:** READY_FOR_WORKER

## Objective and exact evidence
Coordinator ran the required live command against a fresh synthetic PostgreSQL database:
`TEST_DATABASE_URL=<process-local synthetic URL> .venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
Result: `1 failed, 1 passed`, exit 1. The concurrency fixture inserts `UserRole` rows with `granted_by="seed"`, but no matching `users.id = "seed"` exists; PostgreSQL raises a `ForeignKeyViolation` before the concurrent approval requests run.

## Scope
- Allowed implementation file: `backend/tests/test_postgresql.py` only.
- Append a short follow-up section to `.team/tasks/CHPMIS-015-worker-report.md` describing the fixture repair and exact live command result. Do not rewrite prior evidence.
- Do not edit production code, schema, migrations, task index, ledger, environment files, or other tests. Do not drop/reset a database or remove any rows/resources. Preserve all unrelated work.
- Use the existing dedicated synthetic database `chpmis015_test` only when `TEST_DATABASE_URL` is supplied by the Coordinator. Do not print connection values.

## Required correction
Give every synthetic role grant in the fixture a `granted_by` value referencing an existing synthetic `users.id`, preserving valid foreign keys. Keep the test identities unique, retain both approvals as separate concurrent requests against the same pending request, and assert one 200 plus one 409 (or the documented already-decided 409), exactly one resulting role, revoked target session, and one approved decision. Do not loosen assertions to accept an unrelated error such as 400.

## Verification
- Use the existing failing live PostgreSQL result as RED evidence; no destructive reset is permitted.
- Once fixture code is corrected, Coordinator will rerun the live PostgreSQL command against the same dedicated synthetic test database. Worker may run only the repository-defined command `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` if `TEST_DATABASE_URL` is explicitly supplied in the Worker process.
- Run from `backend`: `.venv\Scripts\ruff.exe check tests/test_postgresql.py` and `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py`.
- From repository root: `git diff --check -- backend/tests/test_postgresql.py`.
- Report exact outputs and exit codes; do not claim concurrency PASS before a live PostgreSQL rerun.

## Required real prompt template
- prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, found and retrieved via installed prompt-lookup on 2026-10-31: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Task adaptation: “Act as a senior Python/PostgreSQL test engineer. Fix only the CHPMIS-015 synthetic PostgreSQL concurrency fixture so all FK references point to existing unique synthetic users. Keep the same-request concurrency and strict one-success/one-conflict assertions. Preserve schema and all existing data; run only the scoped test/lint/format commands and append evidence to the existing worker report. Do not commit.”

## Stop conditions
If safe verification would require dropping data, resetting the database, changing production schema/policy, or any edit beyond this scope, stop and report `BLOCKED`.
