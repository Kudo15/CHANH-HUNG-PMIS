# CHPMIS-015 — Live PostgreSQL runtime evidence

## Isolated environment
- Docker context `desktop-linux`, engine 29.9.2. Coordinator started only Compose project `chpmis015`, PostgreSQL service `db`, using `.env.example` placeholders; `docker compose up -d db` exited 0.
- Project-owned volume `chpmis015_pgdata`; new container `chpmis015-db-1`; container reported healthy. Published PostgreSQL port was verified as `127.0.0.1:5432` only.
- The new default DB initially had 0 public tables. Coordinator created a separate DB named `chpmis015_test` in this new project; `CREATE DATABASE` succeeded. No existing project database was used.
- The test command received `TEST_DATABASE_URL` only in its process environment. No `.env` file, production endpoint, Keycloak, real identities, or external provider was used.

## Live PostgreSQL runs
All test commands ran from `backend` against the same project-owned `chpmis015_test` database. No database reset, drop, or cleanup was run; failed attempts may leave uniquely prefixed synthetic rows in this isolated test DB.

1. Before CHPMIS-015-F1, `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` → `1 failed, 1 passed`, exit 1. Migration/readiness passed; concurrency setup stopped on PostgreSQL `ForeignKeyViolation` because `granted_by="seed"` referenced no user.
2. After CHPMIS-015-F1, the same command → `1 failed, 1 passed`, exit 1. The two competing HTTP requests reached the strict expected `200`/`409` (“already decided”) outcomes, then the test failed its postconditions with SQLAlchemy `DetachedInstanceError` while dereferencing `target_user.id` after its setup session closed.
3. After CHPMIS-015-F2, the same command → `2 passed, 3 warnings`, exit 0. This ran the migration/head/readiness test and real PostgreSQL concurrent-approval test, including one-success/one-conflict assertions and postconditions for exactly one role, target-session revocation, and a single approved request.
4. After F4 changed only decision-time approver reads in `backend/app/auth/routes.py`, Coordinator reran the same command against the existing dedicated DB: `2 passed, 4 warnings in 1.83s`, exit 0. PostgreSQL concurrency and migration/head tests still pass after the final auth change. Pytest also emitted a cache-path permission warning; it did not affect either test result. No database reset/drop/cleanup occurred.

## Database evidence after successful run
- `SELECT version()` → PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2).
- `SELECT version_num FROM alembic_version` → `0005_initial_admin_bootstrap`.
- Public table count → 11.
- The synthetic test identities use unique generated prefixes. Their rows were not removed.

## Limitations and cleanup
- This verifies the single-request concurrency case and transaction behavior on PostgreSQL. It does not verify simultaneous conflicting approvals for different requests targeting the same user, nor any external IdP/browser behavior.
- At closeout, Coordinator ran `docker --context desktop-linux compose --env-file .env.example -p chpmis015 stop` → exit 0. Post-check `docker ... compose ... ps -a` showed `chpmis015-db-1` `Exited (0)`; `docker --context desktop-linux volume inspect chpmis015_pgdata --format '{{.Name}}'` returned `chpmis015_pgdata`. The container is stopped and the project volume is preserved; no other Compose project was inspected or changed.
