# CHPMIS-015-F7 — OpenCode Worker Task

## Role and authority

Act as the OpenCode Backend Worker for CHPMIS-015-F7. The exact route/test scope was approved by the owner on 2026-11-02. Use the existing dirty repository workspace and preserve all pre-existing changes. Real prompt template: prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`; project-modernized prompt is in `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`.

## Objective and allowed files

Serialize distinct pending System Admin grants targeting the same User by locking the existing target User row with `SELECT ... FOR UPDATE` in the same approval transaction before checking for an existing grant. Preserve the current conflict behavior: one 200 and one 409, with exactly one active canonical `system_admin`, one approved request and one pending request, and correct target-session revocation.

Modify only:

- `backend/app/auth/routes.py`
- `backend/tests/test_postgresql.py`

No migrations, schema/models/constraints, data cleanup, broader permission/workflow changes, staging, or commits.

## Mandatory first action: live RED

1. Do not inspect or print environment values, credentials, connection strings, or the synthetic PostgreSQL context. Do not search for environment-variable names, probe ports/services, or start/configure any service.
2. Immediately run this exact command from `backend/` as the first shell command:

   `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`

3. It must capture the expected live duplicate-grant RED (two 200 responses / duplicate canonical role) before any edit. Record output and exit code without URLs or secrets.
4. If the test is skipped, unavailable, denied, or fails to show the expected live RED, stop immediately: do not run any further shell command, including `git status`; do not read more task/source files; do not edit anything. Report `BLOCKED / NOT_VERIFIED` and the exact test result.

## After valid RED only

- Read `AGENTS.md`, `.team/CHARTER.md`, this task, `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`, and `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`. Do not open the F6 Worker report.
- Make the smallest TDD change to the two allowed files. Preserve all authorization checks, request-row locking, response semantics, audit fields, and session behavior. Keep F6's test database namespace isolated. Preserve every database; never drop, reset, truncate, or clean one.
- Run only the following exact commands after the valid RED, recording command, working directory, output, exit, and skips:
  1. From `backend/`: `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`
  2. From `backend/`: `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py`
  3. From `backend/`: `.venv/Scripts/python.exe -m pytest -q`
  4. From `backend/`: `.venv/Scripts/ruff.exe check app/auth/routes.py tests/test_postgresql.py`
  5. From `backend/`: `.venv/Scripts/ruff.exe format --check app/auth/routes.py tests/test_postgresql.py`
  6. From repository root: `git diff --check -- backend/app/auth/routes.py backend/tests/test_postgresql.py`
- A PostgreSQL skip is `NOT_VERIFIED`, never PASS. Request independent review only after live RED/GREEN and scoped acceptance evidence complete. Never self-approve.
- Do not stage, commit, push, merge, deploy, access production, or run any other command.

Finish with exactly these machine-readable lines:

`SUMMARY: <one line: implementation and verification, or exact blocker>`

`ROLE_RESULT: <done|review|blocked>`

## OpenCode attempt result (2026-11-02)

- OpenCode role task run ID `2026-11-02T05-48-44-worker-chpmis-015-f7-target-user-row-lock-7cd6`; role `worker`; status `blocked`; session `ses_e65325bd4ffestuSTizuCN9ONj`; project `D:/ANH VU/Google Drive/VUHOCAI/Project/CHANH HUNG PMIS`; service `http://127.0.0.1:28894`; GUI-visible `true` in OpenCode Desktop. Run directory and ledger: `C:\Users\ANHVU\.opencode\role-runs\runs\2026-11-02T05-48-44-worker-chpmis-015-f7-target-user-row-lock-7cd6` and `C:\Users\ANHVU\.opencode\role-runs`.
- Model used: none surfaced; cost `$0.00`; 10,695 input, 571 output, 857 reasoning tokens; exit code 1 (`ROLE_RESULT: blocked`; OpenCode task outcome succeeded).
- First and only shell command, from `backend/`: `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target` → `1 skipped, 5 deselected, 1 warning in 1.31s`, exit 0. The Worker reported no live duplicate-grant RED and performed no further command, file read, or edit. No environment values or host diagnostics were accessed.
- Coordinator post-run `git status --short --branch` exited 0, with the known `backend/.pytest-temp/` permission warning; compared with the pre-run status, no new paths appeared. No F7 source changes were made by this run.
- Resume: `opencode run --session ses_e65325bd4ffestuSTizuCN9ONj -- "continue"`. GUI: OpenCode Desktop → project `D:/ANH VU/Google Drive/VUHOCAI/Project/CHANH HUNG PMIS` → session `worker: CHPMIS-015-F7 target-user row lock`.
