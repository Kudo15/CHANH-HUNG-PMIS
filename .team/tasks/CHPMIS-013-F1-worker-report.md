# CHPMIS-013-F1 Worker Implementation Report

- **Task ID:** CHPMIS-013-F1
- **Role:** Hermes Backend Worker
- **Date:** 2026-11-01
- **Status:** COMPLETED — Ready for read-only OpenCode verification and independent Hermes Reviewer

## 1. Prompt Citation and Modernization
- **Source Template:** Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- **Modernized Worker Prompt:**
> "Act as the bounded CHPMIS-013 PostgreSQL schema-test and CI-hygiene Worker. Inspect the current migration head and approved 0006 contract. Test first, then update only `test_postgresql.py` to assert head `0006`, 12 tables, important columns/constraints, fresh empty and populated-0005 upgrades, row preservation, and PostgreSQL receipt UPDATE/DELETE trigger rejection. Use only new synthetic task-specific databases and preserve them; never drop/reset databases. Do not use metadata.create_all. Do not alter migration semantics; format revision 0006 only. Fix only the five named Ruff import-order findings. Run only assigned checks, report exact commands, outputs/exits and skip state, and request independent review; do not commit."

## 2. Regression Reproduction (RED Phase)
Before making code changes, baseline checks were executed to observe and document failures:
1. **Ruff Check:**
   - Command: `cd backend && .venv/Scripts/ruff.exe check . ../dev`
   - Exit code: 1
   - Output: 5 `I001` import-order errors identified in `tests/test_auth_policy.py`, `tests/test_dashboard_audit.py`, `tests/test_projects.py`, and `tests/test_tasks_workflow.py`.
2. **Ruff Format Check:**
   - Command: `cd backend && .venv/Scripts/ruff.exe format --check .`
   - Exit code: 1
   - Output: `1 file would be reformatted, 35 files already formatted` (`alembic/versions/0006_bootstrap_trust_boundary.py`).
3. **PostgreSQL Migration Head Test:**
   - Command: `cd backend && .venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py`
   - Exit code: 1
   - Output:
     `FAILED tests/test_postgresql.py::test_postgresql_migration_head_and_readiness`
     `AssertionError: assert '0006_bootstrap_trust_boundary' == '0005_initial_admin_bootstrap'`
     `1 failed, 1 passed, 3 warnings in 2.01s`

## 3. Implementation Details
All changes were strictly constrained to the authorized files:
1. `backend/alembic/versions/0006_bootstrap_trust_boundary.py`:
   - Reformatted with Ruff; every executable statement and migration behavior (including downgrade refusal) preserved byte-for-byte.
2. `backend/tests/test_auth_policy.py`:
   - Reorganized imports to clear the two `I001` violations. No test assertions modified.
3. `backend/tests/test_dashboard_audit.py`:
   - Reorganized imports to clear one `I001` violation. No test assertions modified.
4. `backend/tests/test_projects.py`:
   - Reorganized imports to clear one `I001` violation. No test assertions modified.
5. `backend/tests/test_tasks_workflow.py`:
   - Reorganized imports to clear one `I001` violation. No test assertions modified.
6. `backend/tests/test_postgresql.py`:
   - Updated `EXPECTED_REVISION = "0006_bootstrap_trust_boundary"`.
   - Updated `EXPECTED_TABLES` to exactly 12 tables including `admin_bootstrap_instance_state`.
   - Added `_create_synthetic_test_db(prefix)` to generate unique task-specific database names derived from `TEST_DATABASE_URL` using `CREATE DATABASE`, ensuring no test databases are dropped or reset.
   - Enhanced `test_postgresql_migration_head_and_readiness` to assert initial empty state (0 tables), head migration (12 tables), and verify columns, unique constraints, and foreign keys across `admin_bootstrap_instance_state`, `admin_bootstrap_receipts`, `user_roles`, `project_members`, and `tasks`.
   - Added `test_postgresql_upgrade_from_0005_with_synthetic_rows_preserves_data` proving empty -> 0005 migration -> synthetic row insertion (`users`, `admin_bootstrap_receipts`, `user_roles`) -> 0006 head upgrade, verifying data preservation and NULL initialization for new 0006 metadata columns.
   - Added `test_postgresql_receipt_immutability_trigger_blocks_mutations` inserting a synthetic receipt on head schema and proving PostgreSQL triggers block both UPDATE and DELETE mutations while preserving the receipt unchanged.
   - Updated `test_postgresql_concurrent_approval_serialized` to execute against its own dedicated synthetic database.

## 4. Verification Evidence (GREEN Phase)

### Command 1: Live PostgreSQL Tests
- **Command:** `cd backend && .venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py`
- **Working directory:** `backend`
- **Exit code:** 0
- **Output:**
```
....                                                                     [100%]
4 passed, 6 warnings in 3.06s
```
- **Skip status:** 0 skipped (all 4 tests ran against the live PostgreSQL container `chpmis-gate-20261101-db-1`).

### Command 2: Full Backend Test Suite
- **Command:** `cd backend && .venv/Scripts/python.exe -m pytest -q`
- **Working directory:** `backend`
- **Exit code:** 0
- **Output:**
```
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
145 passed, 6 warnings in 9.45s
```
- **Skip status:** 0 skipped (145 passed).

### Command 3: Full Backend & Dev Ruff Lint
- **Command:** `cd backend && .venv/Scripts/ruff.exe check . ../dev`
- **Working directory:** `backend`
- **Exit code:** 0
- **Output:**
```
All checks passed!
```

### Command 4: Backend Ruff Format Check
- **Command:** `cd backend && .venv/Scripts/ruff.exe format --check .`
- **Working directory:** `backend`
- **Exit code:** 0
- **Output:**
```
36 files already formatted
```

### Command 5: Offline Alembic Migration SQL
- **Command:** `cd backend && .venv/Scripts/python.exe -m alembic upgrade head --sql`
- **Working directory:** `backend`
- **Exit code:** 0
- **Output:** Full SQL generated cleanly through `0006_bootstrap_trust_boundary` including table creation, trigger function, and trigger definition.

### Command 6: Local Docker Compose Configuration Validation
- **Command:**
```bash
POSTGRES_PASSWORD=synthetic_ci_only \
DATABASE_URL=postgresql+psycopg://pmis_dev:synthetic_ci_only@db:5432/pmis_dev \
KC_BOOTSTRAP_ADMIN_PASSWORD=synthetic_ci_only \
OIDC_CLIENT_SECRET=synthetic_ci_only \
KC_SYNTHETIC_ADMIN1_PASSWORD=synthetic_ci_only \
KC_SYNTHETIC_ADMIN2_PASSWORD=synthetic_ci_only \
docker compose config --quiet
```
- **Working directory:** Repository root
- **Exit code:** 0
- **Output:** (clean exit 0)

### Command 7: Git Diff & Whitespace Verification
- **Command:** `git diff --check HEAD -- backend/`
- **Working directory:** Repository root
- **Exit code:** 0
- **Output:** Clean, zero whitespace issues introduced in backend files.
*(Note: pre-existing trailing whitespace in `.team/ledger.md:482` was untouched as it is outside the worker allowlist).*

## 5. Scope & Safety Confirmation
- No changes to migration semantics or application behavior.
- Downgrade refusal in `0006_bootstrap_trust_boundary.py` preserved.
- No `metadata.create_all` substituted for live migrations.
- No databases or volumes were dropped or reset; all synthetic test databases are preserved under `chpmis_013_*`.
- No credentials, secrets, or `.env` files touched.
- No git commits or branches created.
