ROLE: verifier (independent, read-only)

Task ID: CHPMIS-012-F1. The owner explicitly approved sending this exact read-only verification payload to OpenCode `role-verifier` through `http://127.0.0.1:28894` on 2026-11-02.

Read `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md` and `.team/tasks/CHPMIS-012-F1-worker-report.md`. Verify the F1-specific changes in the current repository checkout against the approved task pack. The repository has pre-existing unrelated dirty changes, especially in `backend/app/auth/routes.py` and `backend/tests/test_postgresql.py`; do not attribute those to F1 or modify anything.

Run only the seven commands listed under `Verification commands` in the F1 task pack, with their specified working directories:
1. From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
3. From `backend/`: `.venv\Scripts\python.exe -m pytest -q`
4. From `backend/`: `.venv\Scripts\ruff.exe check . ../dev`
5. From `backend/`: `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`
6. From `backend/`: `.venv\Scripts\python.exe -m alembic upgrade head --sql`
7. From repository root: `git diff --check`

Do not inspect, print, or probe `TEST_DATABASE_URL` or any environment value. Record a PostgreSQL skip only as NOT_VERIFIED. Do not run Docker, Keycloak, external-provider calls, extra tests, mutating formatters, write commands, or repository cleanup commands. Do not alter files, index, HEAD, or branch.

Report every command, working directory, result/exit code, PostgreSQL skip status, any verification findings, and whether the scoped diff has unexpected files. End with exactly:
SUMMARY: <one line>
ROLE_RESULT: done|review|blocked
