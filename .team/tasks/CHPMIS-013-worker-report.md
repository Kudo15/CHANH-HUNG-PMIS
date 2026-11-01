# CHPMIS-013 — Worker Implementation Report

- **Task ID:** CHPMIS-013
- **Role:** Hermes Worker (implementation)
- **Prompt template:** Feature coding template, Onyekachi Ibekwe, prompts.chat ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved 2026-10-31
- **Status:** IMPLEMENTATION_COMPLETE — review requested
- **Date:** 2026-10-31

---

## 1. Scope and Allowlist Adherence

The Worker modified exclusively the files permitted in the task pack allowlist:
1. `backend/tests/test_postgresql.py` — updated head revision to `0005_initial_admin_bootstrap` and table contract to 11 tables including `admin_bootstrap_receipts`; retained `TEST_DATABASE_URL` gating and test structure.
2. `backend/alembic/versions/0005_initial_admin_bootstrap.py` — formatting only via `ruff format`; zero semantic or schema change.
3. `backend/tests/test_projects.py` — formatting only via `ruff format`; resolved the single multi-line query call format violation.
4. `.github/workflows/ci.yml` — added synthetic process-local interpolation values (`KC_BOOTSTRAP_ADMIN_PASSWORD`, `OIDC_CLIENT_SECRET`, `KC_SYNTHETIC_ADMIN1_PASSWORD`, `KC_SYNTHETIC_ADMIN2_PASSWORD`) scoped strictly to the Compose validation step.
5. `.team/tasks/CHPMIS-013-worker-report.md` — this report (append-only).

All pre-existing dirty changes from CHPMIS-014 and prior tasks were strictly preserved. No commits, resets, stashes, or push operations were performed.

---

## 2. Audit Finding Remediation and Evidence

### A1-01: PostgreSQL Schema and Migration Head Contract
- In `backend/tests/test_postgresql.py`:
  - `EXPECTED_REVISION` updated from `"0004_projects_tasks_audit"` to `"0005_initial_admin_bootstrap"`.
  - `EXPECTED_TABLES` updated to include `"admin_bootstrap_receipts"`, bringing the exact table count to 11 tables:
    - `alembic_version`
    - `users`
    - `user_roles`
    - `sessions`
    - `oidc_states`
    - `system_admin_requests`
    - `projects`
    - `project_members`
    - `tasks`
    - `audit_events`
    - `admin_bootstrap_receipts`
- Offline Alembic DDL inspection (`python -m alembic upgrade head --sql`) confirmed the 11-table schema and migration head.

### A1-02: Compose Validation Interpolation in CI
- `compose.yaml` specifies mandatory non-empty interpolation checks for Keycloak variables (`${KC_BOOTSTRAP_ADMIN_PASSWORD:?...}`, etc.).
- Reproduction before change:
  - Command: `POSTGRES_PASSWORD=synthetic_ci_only DATABASE_URL=postgresql+psycopg://pmis_dev:synthetic_ci_only@db:5432/pmis_dev docker compose config --quiet`
  - Result: Exit 1, failing on missing `KC_BOOTSTRAP_ADMIN_PASSWORD`, `KC_SYNTHETIC_ADMIN1_PASSWORD`, `KC_SYNTHETIC_ADMIN2_PASSWORD`, and `OIDC_CLIENT_SECRET`.
- Remediation:
  - Added synthetic values `synthetic_ci_only` for the four required variables in `.github/workflows/ci.yml` under the `Validate local Compose configuration` step.
- Reproduction after change:
  - Command: `POSTGRES_PASSWORD=synthetic_ci_only DATABASE_URL=postgresql+psycopg://pmis_dev:synthetic_ci_only@db:5432/pmis_dev KC_BOOTSTRAP_ADMIN_PASSWORD=synthetic_ci_only OIDC_CLIENT_SECRET=synthetic_ci_only KC_SYNTHETIC_ADMIN1_PASSWORD=synthetic_ci_only KC_SYNTHETIC_ADMIN2_PASSWORD=synthetic_ci_only docker compose config --quiet`
  - Result: Exit code 0, completely silent and valid.

### A1-03: Ruff Formatting Violations
- Applied `backend/.venv/Scripts/ruff.exe format` to:
  - `backend/alembic/versions/0005_initial_admin_bootstrap.py` (line 56 `batch_op.add_column(...)`)
  - `backend/tests/test_projects.py` (line 480 `db.query(ProjectMember)...`)
- Re-ran `ruff format --check .` in `backend/`:
  - Output: `35 files already formatted`
  - Exit code: 0
- Re-ran `ruff check . ../dev` in `backend/`:
  - Output: `All checks passed!`
  - Exit code: 0

### A1-04: Downgrade Boundary Analysis (0005 -> 0004)
- Migration inspection of `backend/alembic/versions/0005_initial_admin_bootstrap.py`:
  - Upgrade makes `user_roles.granted_by` nullable (`ALTER TABLE user_roles ALTER COLUMN granted_by DROP NOT NULL;`) and adds `bootstrap_receipt_id`.
  - Downgrade executes:
    1. `ALTER TABLE user_roles DROP CONSTRAINT fk_user_roles_bootstrap_receipt_id;`
    2. `ALTER TABLE user_roles DROP COLUMN bootstrap_receipt_id;`
    3. `ALTER TABLE user_roles ALTER COLUMN granted_by SET NOT NULL;`
    4. `DROP TABLE admin_bootstrap_receipts;`
- Boundary observation:
  - When bootstrap administration is executed via `bootstrap_admins.py`, system admin user roles are created with `granted_by = None` (NULL in SQL).
  - Step 3 of downgrade (`ALTER COLUMN granted_by SET NOT NULL`) will fail on PostgreSQL with `NotNullViolation` (SQLSTATE `23502`: `column "granted_by" of relation "user_roles" contains null values`) if any bootstrap-created rows remain.
  - Therefore, downgrade from revision 0005 to 0004 is **UNSAFE** and will fail when bootstrap admin rows exist.
  - In accordance with the task pack directives, migration semantics have not been modified, and rollback is explicitly reported as unsafe/unverified.

---

## 3. Verification Commands and Exact Results

### From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend`
   - Output: `1 skipped, 1 warning in 1.45s`
   - Exit code: 0 (skipped due to unset `TEST_DATABASE_URL`)

2. `.venv\Scripts\python.exe -m pytest -q`
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend`
   - Output: `100 passed, 1 skipped, 1 warning in 5.52s`
   - Exit code: 0

3. `.venv\Scripts\ruff.exe check . ../dev`
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend`
   - Output: `All checks passed!`
   - Exit code: 0

4. `.venv\Scripts\ruff.exe format --check .`
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend`
   - Output: `35 files already formatted`
   - Exit code: 0

5. `.venv\Scripts\python.exe -m alembic upgrade head --sql`
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend`
   - Output: Full valid DDL transaction creating tables through `0005_initial_admin_bootstrap`, including `admin_bootstrap_receipts`, nullable `granted_by`, and receipt FK constraint.
   - Exit code: 0

### From repository root (`D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`):

6. `docker compose config --quiet` (with synthetic environment contract)
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`
   - Environment:
     - `POSTGRES_PASSWORD=synthetic_ci_only`
     - `DATABASE_URL=postgresql+psycopg://pmis_dev:synthetic_ci_only@db:5432/pmis_dev`
     - `KC_BOOTSTRAP_ADMIN_PASSWORD=synthetic_ci_only`
     - `OIDC_CLIENT_SECRET=synthetic_ci_only`
     - `KC_SYNTHETIC_ADMIN1_PASSWORD=synthetic_ci_only`
     - `KC_SYNTHETIC_ADMIN2_PASSWORD=synthetic_ci_only`
   - Output: (none, quiet mode)
   - Exit code: 0

7. `git diff --check`
   - Working directory: `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`
   - Output: (none, clean diff)
   - Exit code: 0

---

## 4. Limitations and Boundaries

- **Live PostgreSQL Runtime:** Per the Coordinator scope reminder delivered mid-run, Coordinator owns the `chpmis013` live PostgreSQL and Compose runtime execution and evidence. Worker did not inspect, start, or stop Docker or live containers.
- **Downgrade Safety:** Downgrade from 0005 to 0004 with populated bootstrap admin data (`granted_by IS NULL`) is structurally unsafe due to `ALTER COLUMN granted_by SET NOT NULL;` without backfill or cleanup.
- **Allowlist and Git Status:** All changes are strictly confined to the allowlist. No git commits or stage operations performed.
