# CHPMIS-015-F7 — Independent Hermes Reviewer

## ROLE: reviewer (read-only)

Judge the F7 implementation; do not edit, stage, commit, or run tests. Read the requirement and inspect the scoped diff/code. Do not read environment values, credentials, or container configuration. Preserve every existing workspace change. Return `APPROVED` or `CHANGES_REQUESTED`; findings must include `file:line`, priority P1/P2/P3, issue, and correction direction.

## Requirement and scope

Owner approved CHPMIS-015-F7 target-row serialization. Change scope is only:

- `backend/app/auth/routes.py`
- `backend/tests/test_postgresql.py`

The code change should lock the existing target `User` row with `SELECT ... FOR UPDATE` within the same approval transaction and before the existing-role check. It must preserve the existing request-row lock, actor/requester authorization checks, one-200/one-409 conflict behavior, audit fields, and session revocation. No schema, migration, constraint, permission, bootstrap, or broader workflow change is allowed.

The focused PostgreSQL test must cover two distinct pending grant requests for the same target and assert exactly one 200 and one 409, exactly one active canonical `system_admin`, one approved and one pending request, and target-session revocation. Its F6 database name must use an `chpmis_015_f6_` prefix. Review the synchronization hook for determinism, missed-barrier handling, and deadlock risk after the target-row lock.

Important workspace context: both allowed files contain pre-existing unrelated edits from earlier tasks. The recent F1 changes in `routes.py` and existing PostgreSQL test/migration changes predate this F7 Worker. Do not attribute those to F7 or request destructive cleanup. Focus your verdict on the target-row lock and F7 regression-test additions, while flagging any unintended F7 change if identifiable.

Read these records: `AGENTS.md`, `.team/CHARTER.md`, `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`, `.team/tasks/CHPMIS-015-F7-codex-worker.md`, `.team/tasks/CHPMIS-015-F7-reproduction-diagnosis.md`, `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`.

Coordinator's live evidence (already recorded; do not rerun): focused F7 test `1 passed, 5 deselected, 2 warnings in 2.69s`, PostgreSQL module `6 passed, 9 warnings in 5.01s`, full backend suite `159 passed, 9 warnings in 12.46s`, Ruff check/format and scoped `git diff --check` all exit 0.

Finish with one Hermes kanban result: `APPROVED` with evidence or `CHANGES_REQUESTED` with concrete required corrections. Do not commit.
