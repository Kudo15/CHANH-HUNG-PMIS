# CHPMIS-013-F1 — Current Head Schema Gate and Backend CI Hygiene

## Task identity
- **Task ID:** CHPMIS-013-F1
- **Role:** Hermes Backend Worker; then OpenCode read-only verifier and separate Hermes Reviewer
- **Parent:** CHPMIS-013 PostgreSQL schema, migration, and CI contract
- **Status:** IN REVIEW — worker changes complete; schema constraint coverage requires reviewer confirmation; no migration semantics or schema changes are authorized here.
- **Trace:** mission §3, Priority 1; acceptance schema gate; existing CHPMIS-013 contract.

## Objective
Bring the PostgreSQL test contract forward to the existing approved migration head `0006_bootstrap_trust_boundary`, prove empty and populated `0005` upgrades on fresh synthetic PostgreSQL databases, verify important schema/receipt-trigger behavior, and clear the reproduced Ruff/format failures without changing application or migration semantics.

## Files in scope
- `backend/tests/test_postgresql.py` — revision/table/column/constraint contract plus live PostgreSQL-only empty and populated-0005 upgrade tests and immutable receipt trigger assertions.
- `backend/alembic/versions/0006_bootstrap_trust_boundary.py` — formatting only; preserve every executable statement and migration behavior byte-for-byte apart from formatting.
- `backend/tests/test_auth_policy.py`
- `backend/tests/test_dashboard_audit.py`
- `backend/tests/test_projects.py`
- `backend/tests/test_tasks_workflow.py`
- Append `.team/tasks/CHPMIS-013-F1-worker-report.md` only.

No other file, migration semantics, model/schema changes, CI weakening, `metadata.create_all`, new dependency, real identity/data, DB reset/drop, `.env`, or commit. Keep schemas/databases created by tests synthetic and task-specific; preserve them. Existing CHPMIS-013/CHPMIS-010 containers, databases, and volumes must remain untouched.

## Required work
1. Update PostgreSQL test constants/assertions to head revision `0006_bootstrap_trust_boundary` and exactly 12 tables including `alembic_version` and `admin_bootstrap_instance_state`.
2. Assert important head-schema columns, unique and FK constraints, and receipt metadata columns. Record whether the approved schema defines any check constraints; do not invent a new check constraint if none exists.
3. On distinct fresh databases inside the dedicated synthetic PostgreSQL test server, prove: empty database → head; and revision `0005_initial_admin_bootstrap` with synthetic rows → head while preserving those rows. Do not downgrade `0006`, reset any DB, or substitute SQLite/offline SQL/`metadata.create_all` for live migration evidence. If tests need database creation, use only newly generated task-specific names derived from `TEST_DATABASE_URL`; never drop them.
4. Insert a synthetic receipt in a fresh head database and prove both UPDATE and DELETE are blocked by the PostgreSQL immutability trigger; verify the receipt remains.
5. Fix only the five currently reproduced Ruff I001 errors in `test_auth_policy.py`, `test_dashboard_audit.py`, `test_projects.py`, and `test_tasks_workflow.py`; formatting/import edits only, no assertion changes outside the PostgreSQL test acceptance above.
6. Format migration `0006_bootstrap_trust_boundary.py` only. Preserve its behavior and the deliberate downgrade refusal.
7. Record a regression-first sequence for the stale schema assertions/trigger contract; do not report any PostgreSQL check PASS when it skipped.

## Verification commands
From `backend/`:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` (must run against the dedicated live PostgreSQL service; a skip is NOT PASS).
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check .`
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql` (supplemental offline SQL only).
From repository root:
6. `docker compose config --quiet` with only the exact synthetic values from `.github/workflows/ci.yml` in process environment; do not start services from this command.
7. `git diff --check`

Coordinator owns creation/running of the dedicated live PostgreSQL service and records its version, task-specific DB names, starting/final revisions, schema/data preservation, trigger denials, and cleanup state. No database or volume is dropped. After Worker completion, OpenCode independently runs the listed repository checks read-only and a separate Hermes Reviewer inspects the complete relevant diff. If any command is denied, record the block and do not bypass the harness.

## Required prompt template
- Found/retrieved via installed `.agents/skills/prompt-lookup` from prompts.chat: **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as the bounded CHPMIS-013 PostgreSQL schema-test and CI-hygiene Worker. Inspect the current migration head and approved 0006 contract. Test first, then update only `test_postgresql.py` to assert head `0006`, 12 tables, important columns/constraints, fresh empty and populated-0005 upgrades, row preservation, and PostgreSQL receipt UPDATE/DELETE trigger rejection. Use only new synthetic task-specific databases and preserve them; never drop/reset databases. Do not use metadata.create_all. Do not alter migration semantics; format revision 0006 only. Fix only the five named Ruff import-order findings. Run only assigned checks, report exact commands, outputs/exits and skip state, and request independent review; do not commit.”

## Definition of Done
- Live PostgreSQL empty and populated-0005 upgrades reach 0006; data preservation, head schema and both receipt mutation denials are observed with exact evidence.
- Full backend Ruff lint and format pass; backend tests pass with all required PostgreSQL tests actually run, not skipped; offline SQL and Compose validation recorded.
- No schema/app behavior changed, no downgrade protection removed, no destructive DB action, no out-of-scope file.
- OpenCode verifier and independent Hermes Reviewer results are recorded for the same final diff; Coordinator appends all runtime evidence and ledger entry.

## Hermes card closing contract
ROLE: worker (implementation). Work only in this task's workspace. Keep roles serialized. Post progress with `kanban_comment`. Finish with exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; cite changed files, exact results/exits, PostgreSQL skip/pass status, requirement trace, and remaining limits. Do not commit.
