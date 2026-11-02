ROLE: verifier (independent, read-only)

Task ID: CHPMIS-012-F1 final verification after Worker runs 110, 112 (R2), and 113 (R3). The owner approved this exact F1 verification payload for OpenCode `role-verifier` at `http://127.0.0.1:28894`, including the seven original F1 checks. Read only the approved task/evidence files and scoped F1 diff; do not modify anything.

Approved inputs:
- `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`
- `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`
- `.team/tasks/CHPMIS-012-F1-R3-test-scope-cleanup.md`
- `.team/tasks/CHPMIS-012-F1-worker-report.md`
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md` (includes R3 correction/evidence appendices)
- `.team/tasks/CHPMIS-012-F1-independent-review.md` and `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md` if the latter exists at dispatch time
- The scoped F1 changes in `backend/app/auth/oidc.py`, F1 `/login` and `/callback` cookie glue only in `backend/app/auth/routes.py`, `backend/app/auth/models.py`, `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`, `backend/tests/test_auth_oidc.py`, and F1 migration-head/preservation additions only in `backend/tests/test_postgresql.py`.

The repository has pre-existing unrelated dirty work (notably other role/approval changes in `routes.py` and other tests). Do not attribute or inspect unrelated changes as part of this task. Do not modify files, index, HEAD, or branch. Do not inspect, print, or probe `TEST_DATABASE_URL` or any environment value. Do not run Docker, Keycloak, network/provider calls, extra checks, mutating formatters, or cleanup commands.

Run only the seven original F1 commands below, using exactly the listed working directories:

1. From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
3. From `backend/`: `.venv\Scripts\python.exe -m pytest -q`
4. From `backend/`: `.venv\Scripts\ruff.exe check . ../dev`
5. From `backend/`: `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`
6. From `backend/`: `.venv\Scripts\python.exe -m alembic upgrade head --sql`
7. From repository root: `git diff --check`

Record exact command, working directory, output summary, and exit code separately. A PostgreSQL skip due the unset test URL is `NOT_VERIFIED`, not PASS; do not read the environment to confirm it. The follow-up changes added no migration, but command 2 remains required by the approved F1 pack. If any check is denied/unavailable, report `NOT_VERIFIED` and do not change permissions, settings, model, or provider.

End with exactly:
SUMMARY: <one line>
ROLE_RESULT: done|review|blocked

## Coordinator dispatch outcome

- OpenCode run ID: `2026-11-02T02-53-03-verifier-chpmis-012-f1-final-read-only-verificati-467b`; session: `ses_e65d32f1dffeM2T6lVRoAa88Nj`.
- The verifier read the approved task/evidence inputs. Its `shell` tool was denied at the role permission level (`Permission denied: shell`); it executed none of the seven commands. It reported `ROLE_RESULT: blocked`. No command process exit codes exist, so every command below is `NOT_VERIFIED`.
- No shell permission, provider, model, or verifier setting was changed. Run metadata is under the local OpenCode role-run store; no environment values were inspected.

| # | Approved command | Working directory | Result |
|---|---|---|---|
| 1 | `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py` | `backend/` | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
| 2 | `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` | `backend/` | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
| 3 | `.venv\Scripts\python.exe -m pytest -q` | `backend/` | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
| 4 | `.venv\Scripts\ruff.exe check . ../dev` | `backend/` | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
| 5 | `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py` | `backend/` | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
| 6 | `.venv\Scripts\python.exe -m alembic upgrade head --sql` | `backend/` | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
| 7 | `git diff --check` | repository root | `NOT_VERIFIED` — shell permission denial before execution; no process exit code |
