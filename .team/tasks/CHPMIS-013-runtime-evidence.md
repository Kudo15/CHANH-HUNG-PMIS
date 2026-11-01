# CHPMIS-013 — Coordinator Runtime Evidence

- **Task:** CHPMIS-013, A1-01 through A1-04, AC-01/03/04
- **Role:** Codex Coordinator / synthetic runtime verifier
- **Date:** 2026-10-31
- **Branch / baseline:** `audit-remediation/verify-audit-findings` / `a986d31063c52d0ea99cec164d8e5c58b1afa3e1`
- **Data boundary:** Only task-created synthetic databases, users and credentials. No `.env` file existed (`Test-Path .env` → `False`); no `.env` contents were read. `chpmis010` was not queried, changed, stopped or removed.

## Preflight and isolated stack

| Check | Command / observation | Result |
|---|---|---|
| Docker CLI | `docker --version` | Docker 29.9.2, exit 0 |
| Context | `docker context show` | `desktop-linux`, exit 0 |
| Engine | `docker --context desktop-linux info --format '{{.ServerVersion}}'` | 29.9.2, exit 0 after starting the already-installed Docker Desktop hidden (PID 37548) |
| Existing CHPMIS-013 containers/volumes | `docker ... ps -a --filter label=com.docker.compose.project=chpmis013`; matching `volume ls` | none before run, both exit 0 |
| Required host ports | `Get-NetTCPConnection -State Listen -LocalPort 5432,8000,5173,8081` | no listeners before run |
| Isolated stack | `docker --context desktop-linux compose --env-file .env.example -p chpmis013 up --build -d` with process-only synthetic values | exit 0; created `chpmis013_default`, `chpmis013_pgdata`, and only this project's db/backend/frontend containers |
| Health | `docker ... compose -p chpmis013 ps --format json` | db healthy, backend healthy, frontend running |
| Published ports | `docker ... inspect --format '{{json .NetworkSettings.Ports}}' chpmis013-db-1 chpmis013-backend-1 chpmis013-frontend-1` | 5432, 8000, 5173 each bind only to `127.0.0.1` |
| HTTP | `Invoke-WebRequest http://127.0.0.1:8000/health/ready`; `Invoke-WebRequest http://127.0.0.1:5173/` | 200 / 200 |

Compose used process-only synthetic values for `POSTGRES_PASSWORD`, `DATABASE_URL`, `KC_BOOTSTRAP_ADMIN_PASSWORD`, `OIDC_CLIENT_SECRET`, `KC_SYNTHETIC_ADMIN1_PASSWORD`, and `KC_SYNTHETIC_ADMIN2_PASSWORD`. No value was printed. Keycloak was not started.

## Empty database upgrade — live PostgreSQL

1. Created new database `chpmis013_empty`; initial public base-table count was 0 (`psql ... information_schema.tables`, exit 0).
2. From `backend/`, set `TEST_DATABASE_URL` only for the test process to the loopback database and ran `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`.
3. Result: `1 passed, 2 warnings in 4.13s`, exit 0. Warnings were the existing Starlette/httpx deprecation and Alembic's missing `path_separator` deprecation.
4. Independent read-only queries recorded PostgreSQL `17.11 (Debian 17.11-1.pgdg12+2)`, revision `0005_initial_admin_bootstrap`, and exactly these 11 tables: `admin_bootstrap_receipts`, `alembic_version`, `audit_events`, `oidc_states`, `project_members`, `projects`, `sessions`, `system_admin_requests`, `tasks`, `user_roles`, `users`.
5. Full backend suite with the same live `TEST_DATABASE_URL`: `101 passed, 2 warnings in 6.23s`, exit 0. The PostgreSQL integration test ran rather than skipping.

## Populated revision-0004 upgrade — live PostgreSQL

1. Created a separate new database `chpmis013_populated` and ran `.venv\Scripts\python.exe -m alembic upgrade 0004_projects_tasks_audit` with process-only `DATABASE_URL`; exit 0.
2. Before seeding, read-only queries returned revision `0004_projects_tasks_audit` and 10 public base tables.
3. Inserted two synthetic users (`synthetic:chpmis013-target`, `synthetic:chpmis013-grantor`) and one synthetic ordinary `member` role row with a non-null grantor. Insert result: 2 users, 1 role; no real identities.
4. Ran `.venv\Scripts\python.exe -m alembic upgrade head` with process-only `DATABASE_URL`; exit 0.
5. Read-only queries recorded revision `0005_initial_admin_bootstrap`, the same exact 11-table set listed above, and row counts `2 users / 1 user_roles / 0 admin_bootstrap_receipts`. Existing synthetic rows survived the upgrade.

## Downgrade after bootstrap-like nullable grant

1. On only `chpmis013_populated`, changed the synthetic role row's `granted_by` to NULL (`UPDATE 1`, exit 0); a read-only query confirmed one NULL grant.
2. Ran `.venv\Scripts\python.exe -m alembic downgrade 0004_projects_tasks_audit` against that database. **Expected failure observed**, exit 1: `psycopg.errors.NotNullViolation: column "granted_by" of relation "user_roles" contains null values`; SQL was `ALTER TABLE user_roles ALTER COLUMN granted_by SET NOT NULL`.
3. Read-only post-failure queries returned revision `0005_initial_admin_bootstrap`, all 11 tables still present, and `1` of `1` role rows with `granted_by IS NULL`. The failed PostgreSQL transaction did not partially downgrade the schema.
4. Conclusion: downgrade 0005 → 0004 is **unsafe while bootstrap-created NULL-grant rows exist**. This finding is confirmed, not fixed. Applied migration semantics were not changed; no rollback-safety claim is made. A safe data-reconciliation or forward-only policy would need its own reviewed follow-up before implementation.

## Independent verification and limitations

- OpenCode verifier `2026-10-31T14-28-57-verifier-chpmis-013-independent-verification-0b63`, session `ses_e6da2e547ffeq5qXpLY1iFMbAo`, GUI listed, cost USD 0, 48,239 input / 2,511 output, model unavailable. It reported backend pytest `100 passed, 1 skipped`, Ruff check, offline Alembic SQL and `git diff --check .` exit 0. These checks ran without `TEST_DATABASE_URL`; the live PostgreSQL result above was run by the Coordinator.
- OpenCode root diff run `2026-10-31T14-34-39-verifier-chpmis-013-final-root-diff-check-715c`, session `ses_e6d9da911ffeI5zA4PAjeG8w3f`, GUI listed, returned provider interruption and driver exit 1. Ledger summary says the command had no output, but no terminal verifier result was produced; do not count as an independent root-level PASS.
- Coordinator ran root `git diff --check`, exit 0, and scoped Ruff format check on the two changed files: `2 files already formatted`, exit 0. Coordinator independently ran CI-equivalent `docker ... compose -p chpmis013 config --quiet` with synthetic process environment; exit 0.
- A broader formatter invocation from the repository root (not the task/CI command) found a separate existing formatting issue in `dev/keycloak/generate_synthetic_credentials.py`; that file is outside this task allowlist. The required backend command `.venv\Scripts\ruff.exe format --check .` from `backend/` returned `35 files already formatted`, exit 0. The unrelated file was left unchanged.
- Worker/OpenCode offline tests without PostgreSQL report `100 passed, 1 skipped`; only the Coordinator's database-backed full suite produced `101 passed`.
- Remote GitHub CI, authenticated Keycloak/browser E2E, agency IdP, and production remain NOT_VERIFIED / NOT_APPROVED. The CHPMIS-013 stack and named volume are preserved for review; no stop/removal has been performed yet.

## Independent Hermes Review

- Reviewer card `t_23585fca`, task `CHPMIS-013-R1`, run #64, separate session `20261031_214227_522ea7`, profile `default`, no model/provider override; model, usage metrics and explicit GUI visibility unavailable.
- Verdict: `APPROVED` with 0 P1, 0 P2, 0 P3. Reviewer inspected the scoped diff and Worker/runtime evidence read-only; it confirmed the exact 11-table contract, step-scoped synthetic CI values, formatting-only migration/test edits, populated upgrade/data preservation, and the confirmed unsafe downgrade limitation. Remote CI, real IdP/browser E2E and production remain NOT_VERIFIED/NOT_APPROVED. Reviewer made no edits and ran no unassigned tests/runtime operations.

## Post-review resource state

- `docker --context desktop-linux compose --env-file .env.example -p chpmis013 stop` returned exit 0 after review. All three task containers are stopped (`backend` and `db` exited 0; `frontend` exited 1 on stop). No containers or volumes were removed.
- Read-only project-label queries confirm `chpmis013_pgdata` still exists and the `chpmis013` containers remain stopped. Both synthetic databases and all captured evidence remain in that preserved named volume for future inspection.
- Hermes Worker card `t_e5cae42d` was marked complete after Reviewer approval; R1 card `t_23585fca` is done. No commit/push/deploy was made.
