# CHPMIS-013-F1 / CHPMIS-015-F5 OpenCode Final Verification

- **Task ID:** CHPMIS-013-015-T1
- **Role:** OpenCode Tester (read-only)
- **Status:** READY
- **Scope:** Verify only the final candidate in F1/F5 assigned files; make no edits. Keep all task-specific databases and artifacts.
- **DoD:** Run the PostgreSQL schema gate without skips against the local synthetic loopback service; run F5 targeted/auth tests and full backend suite; run Ruff and diff checks. Report exact commands, output, exit code, and GUI/session metadata. Do not count a skipped PostgreSQL test as a pass.
- **Requirement trace:** `.team/tasks/CHPMIS-013-F1-current-head-schema-gate.md`; `.team/tasks/CHPMIS-015-F5-canonical-decision-authority.md`.
- **Prompt template:** Not applicable; read-only Tester task.

## Commands

Set `TEST_DATABASE_URL` and `DATABASE_URL` only for the test command process to the synthetic loopback URL `postgresql+psycopg://pmis_test:synthetic_ci_only@127.0.0.1:5432/pmis_test`. The service is `chpmis-gate-20261101-db-1` on `127.0.0.1:5432`.

1. `.venv/Scripts/python.exe -c "import os,sys,pytest; u='postgresql+psycopg://pmis_test:synthetic_ci_only@127.0.0.1:5432/pmis_test'; os.environ['TEST_DATABASE_URL']=u; os.environ['DATABASE_URL']=u; sys.exit(pytest.main(['-q','tests/test_postgresql.py']))"`
2. `.venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py -k legacy_role`
3. `.venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py`
4. Run the full suite with the same process-local synthetic DB environment as command 1: `.venv/Scripts/python.exe -c "import os,sys,pytest; u='postgresql+psycopg://pmis_test:synthetic_ci_only@127.0.0.1:5432/pmis_test'; os.environ['TEST_DATABASE_URL']=u; os.environ['DATABASE_URL']=u; sys.exit(pytest.main(['-q']))"`.
5. `.venv/Scripts/ruff.exe check . ../dev`
6. `.venv/Scripts/ruff.exe format --check .`
7. `git diff --check HEAD`

The coordinator separately owns live PostgreSQL version/database inventory and Compose/offline Alembic evidence; do not use Docker cleanup or inspect environment variables.
