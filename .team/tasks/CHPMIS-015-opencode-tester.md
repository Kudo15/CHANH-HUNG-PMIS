# CHPMIS-015 — Independent OpenCode verification

- **Task ID:** CHPMIS-015-T1
- **Role:** Independent Tester / Verifier (OpenCode `role-verifier`)
- **Parent task:** CHPMIS-015 / Hermes Worker card `t_47da9e47`, run #66
- **Trace:** A5-01, A5-02, approved HG2; `.team/tasks/CHPMIS-015-system-admin-transaction.md`
- **Status:** COMPLETE — OpenCode verifier run `2026-10-31T15-04-36-verifier-chpmis-015-independent-verification-4b8b`, session `ses_e6d823ee4ffep4PtzAahXrjNLo`, GUI visible, cost $0, 68,063 input / 1,064 output, model unavailable. `ROLE_RESULT: done`; all six assigned checks exited 0. Focused auth 7 passed; PostgreSQL 2 skipped because TEST_DATABASE_URL absent; full suite 102 passed / 2 skipped; Ruff lint/format and scoped diff clean.

## Scope
Read-only verification of the Worker changes in the four assigned backend files. Do not edit files, run application services, set `TEST_DATABASE_URL`, access Docker, or run commands beyond the exact allowlist below. Live PostgreSQL concurrency is Coordinator-owned and will be verified separately against an isolated synthetic database.

## Exact verification commands
Run from `backend`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py`
2. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
3. `.venv\Scripts\python.exe -m pytest -q`
4. `.venv\Scripts\ruff.exe check app/auth/routes.py app/auth/session.py tests/test_auth_remediation.py tests/test_postgresql.py`
5. `.venv\Scripts\ruff.exe format --check app/auth/routes.py app/auth/session.py tests/test_auth_remediation.py tests/test_postgresql.py`

From the `backend` working directory:

6. `git diff --check -- app/auth/routes.py app/auth/session.py tests/test_auth_remediation.py tests/test_postgresql.py`

The OpenCode shell is deny-by-default and only these exact commands will be enabled. Global `edit: deny` and `shell * deny` must remain unchanged. Report each exact command, output, and exit code. A skipped PostgreSQL test is `NOT_VERIFIED`, not a concurrency PASS.

## Final rerun after PostgreSQL fixture follow-ups
`backend/tests/test_postgresql.py` changed after the first OpenCode run because the live PostgreSQL execution exposed two fixture-only issues. Rerun all six exact checks above against the final checkout. Do not set `TEST_DATABASE_URL`; Coordinator has already executed the live PostgreSQL run and records it in `.team/tasks/CHPMIS-015-runtime-evidence.md`. Append the new run ID/session/results here; the earlier independent pass does not cover the later fixture edits.

## Read-only review questions
- Does the approval route use one business transaction for role changes, target-session revocation, and request decision, with rollback on failure?
- Are requester, approver, and target/action conditions revalidated while the pending request is locked?
- Do regression tests exercise rollback and stale authority/state without changing HG2 policy?
- Is the PostgreSQL concurrency test scoped to synthetic unique rows and the dedicated opt-in URL, with no destructive reset/drop?
- Do any failures or diffs violate task scope?

Finish with exactly the role-verifier `SUMMARY:` and `ROLE_RESULT:` lines. Do not fix any issue; report it for Coordinator/Reviewer handling.

### Final rerun result
- Run `2026-10-31T15-18-42-verifier-chpmis-015-final-independent-verificatio-bf22`, session `ses_e6d755166ffeGvywAKok8dL8oK`; OpenCode v2.2.2 / `role-verifier`, GUI visible, model unavailable, cost $0, 54,326 input / 3,460 output; exit 0, `ROLE_RESULT: done`.
- Focused auth: 7 passed; opt-in PostgreSQL suite: 2 skipped because no `TEST_DATABASE_URL` was set in OpenCode; full backend: 102 passed / 2 skipped; Ruff lint and formatting passed; scoped `git diff --check` clean. The skipped OpenCode PG result is not counted as live concurrency evidence; see `.team/tasks/CHPMIS-015-runtime-evidence.md` for Coordinator's PostgreSQL 2-pass result.

### Final rerun after F4 approver revalidation fix
- Run `2026-10-31T15-36-48-verifier-verifier-chpmis-015-final-after-f4-appro-c775`, session `ses_e6d64c56afferMfF0BfirPNVef`; OpenCode v2.2.2, role `verifier`, GUI listed, service `http://127.0.0.1:28894`, model unavailable, cost $0, 72,455 input / 1,871 output; exit 0, `ROLE_RESULT: done`.
- Six exact checks from this task pack: focused auth `8 passed`; PostgreSQL `2 skipped` because `TEST_DATABASE_URL` was not set; full backend `103 passed / 2 skipped`; Ruff lint and format passed; scoped `git diff --check` clean. Live PostgreSQL is recorded separately in this pack's runtime evidence.
