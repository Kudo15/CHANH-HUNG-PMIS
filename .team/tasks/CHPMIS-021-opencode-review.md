# CHPMIS-021 — OpenCode independent evidence review

- **Role:** independent OpenCode Reviewer, read-only.
- **Required session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, `.team/tasks/CHPMIS-021-ac03-current-head-evidence.md`, `docs/MISSION.md` and `ACCEPTANCE.md` before review. Explicitly report each required read. The prior reviewer approved the technical evidence but its session output did not establish that it read the charter; this fresh session must satisfy the full session-start requirement.
- **Task and trace:** CHPMIS-021; AC-03; mission §3.
- **Objective:** Decide whether the Coordinator's captured live PostgreSQL result supports AC-03. Read `.team/tasks/CHPMIS-021-ac03-current-head-evidence.md`, `ACCEPTANCE.md`, and the existing `test_postgresql_migration_head_and_readiness` implementation in `backend/tests/test_postgresql.py`. Inspect the current migration head if needed. Do not run commands against databases, services, or environments. Do not edit files, inspect credentials, or change permissions.
- **Review criteria:** The executed test first checks that the fresh database contains no tables, upgrades via Alembic to current head, then verifies the revision and exact table set. The reported psql inventory must agree with the test contract. Identify any gap preventing AC-03 acceptance, including evidence that is reported but not directly observed by you. Acknowledge that execution was by Coordinator and do not claim an independent runtime rerun.
- **DoD:** Return `APPROVED` or `CHANGES_REQUESTED` with concrete findings and locations; preserve the distinction between evidence review and live rerun. Report exact role result. Do not stage, commit, modify files, or use other agents.

SUMMARY: <one line>
ROLE_RESULT: <done|review|blocked>
