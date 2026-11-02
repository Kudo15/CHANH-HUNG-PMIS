# CHPMIS-012-F1 — Exact-Command Hermes Tester Retry

- **Task ID:** CHPMIS-012-F1-T1-HERMES-RETRY
- **Role:** Independent Tester / Verifier (read-only)
- **Status:** `COMPLETE — SIX CHECKS PASSED; POSTGRESQL NOT_VERIFIED`
- **Harness:** Hermes Agent, default profile; no model/provider override
- **Workspace:** Existing repository directory (preserve all dirty work); no worktree or branch
- **Requirement trace:** CHPMIS-012 / mission §5; AC-05; approved F1 task `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; R2 `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`; R3 `.team/tasks/CHPMIS-012-F1-R3-test-scope-cleanup.md`; final review `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md`.

## Authorization and prior attempt

On 2026-11-02 the owner authorized one fresh Hermes Tester attempt limited to the seven exact commands in this pack. This follows the previous fallback card `t_b6265dce` / run 116, which was interrupted after executing an unapproved `git status`; none of the seven assigned commands ran. Its report is `.team/tasks/CHPMIS-012-F1-hermes-tester-fallback-proposal.md`. Do not reuse or reopen that card.

An earlier broad dispatch mistakenly selected unrelated F3 card `t_e4f5224f` / run 115; it was immediately reclaimed and terminated. For this attempt, the Coordinator will create, claim, and launch only the exact card ID. Do not run any dispatcher or queue command.

## Hard command boundary

**Run exactly the seven commands in the next section and no other shell command.** In particular, do not run `git status`, `git diff`, shell listings, environment inspection, preflight commands, or equivalent. Do not use a shell command to inspect code changes. Read the listed task/evidence files and source files through the available read-only file-reading tools. If any tool or instruction would require another shell command, stop and report `ROLE_RESULT: blocked`; do not improvise.

Do not inspect, print, or probe `TEST_DATABASE_URL` or any environment value. Do not run Docker, Keycloak, network/provider calls, mutating formatters, cleanup commands, or additional tests. Do not change files, index, HEAD, branch, permissions, settings, model, or provider. Do not commit, push, merge, deploy, or access production.

## Approved read-only inputs

- `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`
- `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`
- `.team/tasks/CHPMIS-012-F1-R3-test-scope-cleanup.md`
- `.team/tasks/CHPMIS-012-F1-worker-report.md`
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md` (includes R3 correction/evidence appendices)
- `.team/tasks/CHPMIS-012-F1-independent-review.md`
- `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md`
- `.team/tasks/CHPMIS-012-F1-R2-R3-open-code-verifier.md`
- The scoped F1 changes in `backend/app/auth/oidc.py`, only F1 `/login` and `/callback` cookie glue in `backend/app/auth/routes.py`, `backend/app/auth/models.py`, `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`, `backend/tests/test_auth_oidc.py`, and only F1 migration-head/preservation additions in `backend/tests/test_postgresql.py`.

The workspace has pre-existing unrelated dirty changes, including other behavior in `routes.py` and test files. Do not attribute, inspect, or report those unrelated changes. Distinguish only the F1 slices listed above.

## Exact verification commands

Run each command once, using the stated working directory:

1. From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
3. From `backend/`: `.venv\Scripts\python.exe -m pytest -q`
4. From `backend/`: `.venv\Scripts\ruff.exe check . ../dev`
5. From `backend/`: `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`
6. From `backend/`: `.venv\Scripts\python.exe -m alembic upgrade head --sql`
7. From repository root: `git diff --check`

For each, record the exact command, working directory, output summary, and process exit code. If a command is denied or unavailable, record `NOT_VERIFIED` and no process exit code. A PostgreSQL skip is `NOT_VERIFIED`, not PASS. Do not inspect an environment variable to explain a skip.

## Review and completion contract

Read only the approved task/evidence inputs and scoped F1 source slices above using read-only file tools. Consider whether the code and evidence match the approved F1 behavior; do not broaden review into unrelated route behavior. Provide command-by-command results and scoped findings. Do not claim a full runtime pass if PostgreSQL skipped or any command was not run.

Finish with exactly one Hermes card action:
- `kanban_complete(result=... )` only if the scoped review is complete; clearly retain any PostgreSQL or external runtime `NOT_VERIFIED` limits.
- `kanban_block(reason=... )` if any unauthorized command would be needed, tool access is denied, or the allowed checks cannot be completed.

End the result with exactly:
SUMMARY: <one line>
ROLE_RESULT: done|blocked

## Hermes execution record

- **Card / run:** `t_030b0fcf` / run 118; status `done`; profile `default`; workspace was the existing repository directory. No model/provider override was set. Hermes session: `20261102_122806_796187` (no session ID surfaced in card metadata).
- **Process boundary:** The Tester reported exactly the seven authorized shell commands and zero others; it did not inspect or probe `TEST_DATABASE_URL`, did not change repository files/index/branch/HEAD, and made no network, Docker, or Keycloak calls.

| # | Exact command | Working directory | Result |
|---|---|---|---|
| 1 | `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py` | `backend/` | Exit 0 — 16 passed, 1 warning; PASS |
| 2 | `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` | `backend/` | Exit 0 — 6 skipped, 1 warning; NOT_VERIFIED (no live PostgreSQL evidence) |
| 3 | `.venv\Scripts\python.exe -m pytest -q` | `backend/` | Exit 0 — 153 passed, 6 skipped, 1 warning; suite PASS, PostgreSQL portion NOT_VERIFIED |
| 4 | `.venv\Scripts\ruff.exe check . ../dev` | `backend/` | Exit 0 — all checks passed |
| 5 | `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py` | `backend/` | Exit 0 — six files already formatted |
| 6 | `.venv\Scripts\python.exe -m alembic upgrade head --sql` | `backend/` | Exit 0 — valid DDL generated through `0007_oidc_pkce_browser_binding` |
| 7 | `git diff --check` | repository root | Exit 0 — clean, empty output |

- **Scoped Tester finding:** 0 P1 / 0 P2 / 0 P3 in reviewed F1 slices. Independent Reviewer remains APPROVED (0 findings) per `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md`.
- **Overall F1 status:** Verification is complete for commands that executed; live PostgreSQL remains `NOT_VERIFIED`. F1 is not fully closed because the PostgreSQL evidence is still absent. Actual Keycloak/browser E2E remains outside this F1 pack and tracked downstream.
