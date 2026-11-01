# CHPMIS-014 — OpenCode Independent Tester Contract

Role: read-only independent Tester/Verifier. Do not edit files, apply formatting, fix findings, stage, or commit. Inspect the task pack, Worker report, and scoped diff; then run these exact assigned checks independently:

From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py tests/test_auth_remediation.py`
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check app/auth/bootstrap_admins.py tests/test_admin_bootstrap.py tests/test_auth_remediation.py`

From repository root:

5. `git diff --check`

Report exact commands, outputs, exit codes, test counts/skips, file scope, and any mismatch with the Worker report. SQLite results are not PostgreSQL evidence; `TEST_DATABASE_URL` is unset. If anything fails, report only; do not repair it.
