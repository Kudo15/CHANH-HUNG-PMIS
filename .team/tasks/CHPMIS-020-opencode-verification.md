# CHPMIS-020 — OpenCode Tester and Reviewer Evidence

## Status

Implementation is locally complete and independently approved by the read-only Reviewer. CHPMIS-020 remains `IN_PROGRESS`: the OpenCode Tester could not independently execute backend checks because the role's shell allowlist denied the project virtualenv and Docker commands; remote CI has no configured Git remote and remains `NOT_VERIFIED`.

## Independent Tester

- **Role:** OpenCode `role-verifier` (read-only Tester)
- **Run:** `2026-11-02T11-03-23-verifier-chpmis-020-independent-read-only-tester--2fb5`
- **Session:** `ses_e641e702dfferblGuHWcfY96rx`
- **Status:** `blocked`; service URL `http://127.0.0.1:28894`; GUI visibility confirmed for the CHANH HUNG PMIS project; cost reported `$0`, model not exposed.
- **Scope:** inspected task pack, Worker report, status, diff, and CI/test changes. No source/docs edits, Registry access, or bypass attempts.

| Check | Observed outcome |
|---|---|
| `git status`, `git diff --stat`, per-file `git diff` | Ran; exit 0; product diffs matched Worker summary; pre-existing `.worktrees/` preserved. |
| `git diff --check` | Passed; exit 0. |
| `npm --prefix frontend run lint` | Passed; exit 0. |
| `npm --prefix frontend run test -- --run` | Passed; 3 files, 26 tests; exit 0. |
| `npm --prefix frontend run build` | Passed; TypeScript/Vite build; exit 0. |
| `git remote -v` | No output; no remote configured. |
| `pytest -q tests/test_admin_bootstrap.py -k "windows_registry or win32"` using system Python 3.8.5 | Not a valid project test run; collection failed with `ModuleNotFoundError: No module named 'sqlalchemy'`, exit 1. Not used as a substitute for the project venv. |
| `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py -k "windows_registry or win32"` | Denied by OpenCode shell policy (`Permission denied: shell`); not run. |
| `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py` | Denied by OpenCode shell policy; not run. |
| `.venv\Scripts\ruff.exe check .` and `.venv\Scripts\ruff.exe format --check .` | Denied by OpenCode shell policy; not run. |
| `.venv\Scripts\python.exe -m pytest -q` | Denied by OpenCode shell policy; not run. |
| `.venv\Scripts\python.exe -m alembic upgrade head --sql` | Denied by OpenCode shell policy; not run. |
| `docker compose --env-file .env.example config --quiet` | Denied by OpenCode shell policy; not run. |

Tester records all backend checks and Compose validation as `NOT_VERIFIED`. The original session was stopped before its proposed PowerShell probe; no permission workaround was attempted. RED/GREEN was not independently reproduced.

## Independent Reviewer

- **Role:** OpenCode `role-reviewer` (read-only)
- **Initial run:** `2026-11-02T11-06-00-reviewer-chpmis-020-independent-read-only-review-3a1e`, timed out after 900 seconds without a verdict.
- **Verdict run:** `2026-11-02T11-21-13-reviewer-chpmis-020-reviewer-verdict-from-existin-9dee`
- **Session:** `ses_e640ffbb6ffeCpf42v4EHwzw6c`
- **Status:** `done`; service URL `http://127.0.0.1:28894`; GUI visibility confirmed; cost reported `$0`, model not exposed.
- **Verdict:** `APPROVE` — no blocking code findings. The reviewer inspected the task pack, Worker report, full scoped diff, production reader, tests, CI workflow, and skip/selector context.
- **Evidence:** the reviewer confirmed the one-line `ctypes.c_byte` → `ctypes.c_ubyte` change at `backend/app/auth/bootstrap_admins.py:700`, bounded conversion at line 729, and unchanged non-Windows guard at lines 373–377. It approved platform guard and Win32 test separation, the production-reader high-bit regression, invalid type/length/API-error and cleanup coverage, and the Windows job/selector at `.github/workflows/ci.yml:45–56`.
- **Non-blocking closure gates:** remote CI execution is not observed; independent Tester backend evidence remains partial. Reviewer noted the Worker report's `[x]` checkbox for Windows CI execution despite no observed remote run; the nearby explicit `NOT_VERIFIED` caveat prevents this from being misleading. The reviewer stated CHPMIS-020 cannot be declared complete until the remote CI gate is observed.

## Requirement Trace and Disposition

- **Mission §3 A1/A2 and §6; task pack requirements 1–6:** Worker implementation and local Windows verification are recorded in `.team/tasks/CHPMIS-020-worker-report.md`; independent review approved correctness, fail-closed behavior, test separation, scope, and CI configuration.
- **Task pack independent verification requirement:** Tester result and Reviewer verdict are recorded here and in `.team/ledger.md`. Tester outcome is blocked for backend checks; Reviewer outcome is approved.
- **Remote CI:** `NOT_VERIFIED` — no Git remote is configured, no run exists for the candidate change, and no push or remote was created.
- **Overall:** implementation approved; keep CHPMIS-020 `IN_PROGRESS` pending the task pack's remote CI evidence and any required independent backend re-verification through an authorized environment.

## Coordinator Follow-Up (2026-11-02)

These are read-only Coordinator verification results after the OpenCode role runs. They do not replace independent Tester evidence and made no product-code changes.

| Check | Observed outcome |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py -k "windows_registry or win32"` from `backend/` | Passed: 6 passed, 39 deselected; exit 0. Pytest emitted one cache warning because it could not write to the protected backend cache/temp location. |
| `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py` from `backend/` | Passed: 45 passed; exit 0. Same cache warning. |
| `.venv\Scripts\ruff.exe check .` from `backend/` | Exit 0, “All checks passed”; Ruff also reported access denied while traversing `backend/.pytest-temp`, so traversal was not clean. |
| `.venv\Scripts\ruff.exe format --check .` from `backend/` | Exit 1: access denied for `backend/.pytest-temp`; Ruff reported 37 files already formatted. Full format check is not verified by this run. |
| `.venv\Scripts\python.exe -m pytest -q` from `backend/` | Exit 1: 140 passed, 6 skipped, 3 warnings, 16 setup errors. The 16 errors were `PermissionError: [WinError 5]` while pytest enumerated the default `C:\Users\ANHVU\AppData\Local\Temp\pytest-of-ANHVU` directory for `test_synthetic_credentials.py` fixtures. This is an environment permission failure, not a passing full-suite run. |
| `.venv\Scripts\python.exe -m pytest -q --basetemp <repo>/.team/tasks/pytest-chpmis020-20261102` from `backend/` | Exit 1. The retry still hit access denied for pytest temp directories and failed during session cleanup while enumerating the specified basetemp. The isolated temp directory is now inaccessible and was left untouched. |
| `.venv\Scripts\python.exe -m alembic upgrade head --sql` from `backend/` | Passed; exit 0. |
| `docker compose --env-file .env.example config --quiet` from repo root | Passed; exit 0. |
| `git diff --check` from repo root | Passed; exit 0. |
| `git remote -v` | No output; no remote is configured. |

Coordinator evidence narrows local gaps but does not change the OpenCode Tester status: its backend commands were denied by its shell policy. Remote Windows CI remains `NOT_VERIFIED`, and CHPMIS-020 remains `IN_PROGRESS`.

## Coordinator follow-up — 2026-11-03

The following exact commands were run from `backend/` under reviewed execution, without process-local PostgreSQL settings. They supplement but do not replace independent OpenCode Tester evidence.

| Command | Result |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q` | Exit 0; 156 passed, 7 skipped, 1 warning. The skipped PostgreSQL tests, including the CHPMIS-018 RED reproducer, remain NOT_VERIFIED by this run. |
| `.venv\Scripts\ruff.exe check .` | Exit 0; `All checks passed!` |
| `.venv\Scripts\ruff.exe format --check .` | Exit 0; 37 files already formatted. |

These results close the prior Coordinator-only full-suite and format execution failures for this invocation. They do not establish an independently rerun backend check, a live PostgreSQL suite, or an observed Windows CI run. CHPMIS-020 remains IN_PROGRESS.

OpenCode retry T2 independently passed `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py` (45 passed, 0 skipped, exit 0); the next Ruff command was denied by role shell policy and the role stopped. Remaining retry checks were not executed; details and run metadata: `.team/tasks/CHPMIS-020-opencode-backend-retry.md`.
