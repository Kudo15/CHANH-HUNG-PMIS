# CHPMIS-012-F1-R2 Worker Implementation Report

- **Task ID:** CHPMIS-012-F1-R2
- **Role:** Hermes Worker (implementation)
- **Status:** READY_FOR_REVIEW
- **Requirement Trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; approved F1 task pack `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; accepted route design `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`; task pack `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`
- **Prompt Template:** Real prompts.chat Feature coding template by Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved through `.agents/skills/prompt-lookup` and cited in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`.

---

## 1. Scope and Allowed Files

Modifications were strictly confined to the follow-up task pack allowlist:
- `backend/app/auth/oidc.py`: Replaced load-then-ORM-delete with atomic conditional claim/delete (`db.query(OIDCState).filter(OIDCState.state == state).delete(synchronize_session=False)`). Requiring exactly one affected row before committing and before remote token exchange; rollback and HTTP 400 fail-closed on claim loss. Preserved Browser A transaction retention on missing/mismatched cookie. Added `on_consumed` callback notification upon successful atomic claim commit.
- `backend/app/auth/routes.py`: Coordinated callback route with service to clear the `pmis_oidc_bind` cookie whenever transaction consumption succeeds, including downstream token exchange failure, ID-token validation failure, inactive user failure, and session creation failure. Retained cookie on pre-consumption validation failures (missing/mismatched cookie, expired state, unknown state, failed atomic claim). Preserved existing status codes and details without leaking internal errors or secrets.
- `backend/tests/test_auth_oidc.py`: Added focused regressions covering:
  1. `test_callback_atomic_claim_prevents_stale_reader_double_exchange`: Stale reader with pre-loaded state fails closed with HTTP 400 before token exchange, without double exchange or unhandled `StaleDataError`.
  2. `test_callback_cookie_cleanup_on_downstream_failure_and_retention_on_pre_consumption_rejection`: Browser-binding cookie is deleted on downstream exchange (502) and inactive user (403) failures; cookie is retained on mismatched cookie and unknown state pre-consumption failures.
  3. `test_default_oidc_client_token_request_body_carries_code_verifier`: Verified `DefaultOIDCClient` token request form body carries `code_verifier` using mocked local I/O.
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md`: This report artifact.

All pre-existing dirty files and repository changes were strictly preserved. No schema or migration files were modified.

---

## 2. TDD RED Evidence

Focused test regressions were added to `backend/tests/test_auth_oidc.py` before modifying `backend/app/auth/oidc.py` and `backend/app/auth/routes.py`.

- **Command:** `backend/.venv\Scripts\python.exe -m pytest -q backend/tests/test_auth_oidc.py`
- **Working Directory:** Repository root (`D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`)
- **Exit Code:** `1`
- **Output:**
```
.............FF.                                                         [100%]
================================== FAILURES ===================================
______ test_callback_atomic_claim_prevents_stale_reader_double_exchange _______
...
>               with pytest.raises(HTTPException) as exc_info:
E               Failed: DID NOT RAISE HTTPException
backend\tests\test_auth_oidc.py:865: Failed

_ test_callback_cookie_cleanup_on_downstream_failure_and_retention_on_pre_consumption_rejection _
...
>           assert is_binding_cookie_cleared(resp)
E           assert False
E            +  where False = is_binding_cookie_cleared(<Response [502 Bad Gateway]>)
backend\tests\test_auth_oidc.py:930: AssertionError
============================== warnings summary ===============================
backend\app\auth\oidc.py:355: SAWarning: DELETE statement on table 'oidc_states' expected to delete 1 row(s); 0 were matched.  Please set confirm_deleted_rows=False within the mapper configuration to prevent this warning.
  db.commit()
=========================== short test summary info ===========================
FAILED backend\tests\test_auth_oidc.py::test_callback_atomic_claim_prevents_stale_reader_double_exchange
FAILED backend\tests\test_auth_oidc.py::test_callback_cookie_cleanup_on_downstream_failure_and_retention_on_pre_consumption_rejection
2 failed, 14 passed, 2 warnings in 3.28s
```

---

## 3. TDD GREEN Evidence

After implementing the atomic conditional delete/claim and route cookie cleanup coordination:

- **Command:** `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
- **Working Directory:** `backend/`
- **Exit Code:** `0`
- **Output:**
```
................                                                         [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
16 passed, 1 warning in 2.33s
```

---

## 4. Verification Commands & Results

All 5 required verification commands were executed and reported truthfully:

### 1. Focused OIDC Pytest
- **Command:** `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Summary:** `16 passed, 1 warning in 2.33s`

### 2. Full Backend Pytest Suite
- **Command:** `.venv\Scripts\python.exe -m pytest -q`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Summary:** `153 passed, 6 skipped, 1 warning in 12.06s`

### 3. Ruff Linter Check
- **Command:** `.venv\Scripts\ruff.exe check . ../dev`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Summary:** `All checks passed!`

### 4. Ruff Format Check (Non-Mutating)
- **Command:** `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py tests/test_auth_oidc.py`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Summary:** `3 files already formatted`

### 5. Git Diff Whitespace Check
- **Command:** `git diff --check`
- **CWD:** Repository root (`D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`)
- **Exit Code:** `2`
- **Summary:** Pre-existing `.team/ledger.md:539: trailing whitespace.` was created during task setup prior to worker dispatch. All worker-modified files (`backend/app/auth/oidc.py`, `backend/app/auth/routes.py`, `backend/tests/test_auth_oidc.py`) have zero whitespace errors (`git diff --check backend/` exited 0 with empty output).

### 6. PostgreSQL Status
- **Status:** `NOT_REQUIRED` per task specification (no schema changes or migrations in this follow-up).

---

## 5. Definition of Done Compliance

- [x] Regressions shown RED before implementation and GREEN after.
- [x] Exact allowlist respected: only `backend/app/auth/oidc.py`, `backend/app/auth/routes.py`, `backend/tests/test_auth_oidc.py`, and this report modified.
- [x] All 5 checks executed and reported truthfully with exact working directory, output, and exit code.
- [x] No commit, stage, push, deploy, secret exposure, or forbidden git discard/formatting commands executed.
- [x] Worker requests independent review and does not claim F1 or platform gate is complete.

---

## 6. Remaining Limits

- Live Keycloak OIDC provider integration and JWKS key rotation remain unverified in the local environment.
- Live PostgreSQL runtime and multi-container Docker Compose runtime are not executed in this unit scope.
- Browser-based end-to-end SSO cookie exchange remains deferred to integration testing.
- Platform gate completion remains subject to independent reviewer assessment and human gate approval.

---

## 7. R3 Post-Review Corrections & Process Deviations

This section is appended per task `CHPMIS-012-F1-R3` to record command and CWD deviations from R2 run 112 and document the final root whitespace check status:

1. **R2 Command and CWD Process Deviations:**
   - During TDD RED baseline verification, pytest was invoked from repository root as `backend/.venv\Scripts\python.exe -m pytest -q backend/tests/test_auth_oidc.py` (CWD: repository root) instead of running `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py` from `backend/`.
   - Intermediate test and lint runs were executed using repo-relative paths from repository root (e.g., `backend/.venv/Scripts/python.exe` and root-invoked Ruff) rather than changing directory to `backend/`.
   - When root `git diff --check` exited 2 due to pre-existing trailing whitespace in `.team/ledger.md:539`, an unlisted scoped command variant `git diff --check backend/` was executed from repository root (exited 0) to verify worker-modified files.

2. **Coordinator Ledger Line-Ending Normalization & Exact Root Diff Check:**
   - The failure of root `git diff --check` (exit code 2) was caused by a CRLF line ending appended to `.team/ledger.md:539` by the coordinator during task setup prior to worker dispatch.
   - The coordinator normalized only its own line ending in `.team/ledger.md:539` (converting CRLF to LF); the worker did not modify `.team/ledger.md`.
   - After this coordinator-owned line ending normalization, running the exact required root command `git diff --check` from the repository root passed with exit code `0` and empty output.

3. **Test-Scope Correction:**
   - In `backend/tests/test_auth_oidc.py`, the required positive assertion in `test_default_oidc_client_token_request_body_carries_code_verifier` (verifying that supplied `code_verifier` is propagated in the token request form body) is retained.
   - The unrequested optional `code_verifier=None` omission subcase was removed per CHPMIS-012-F1-R3 scope.


## 8. R3 Exact Execution Evidence and Reporting Corrections

- **R3 card/run:** `t_f518fc67`, run 113, session `20261102_094347_3b4a67`, status `review` after `kanban_request_review`.
- **Scope cleanup:** `backend/tests/test_auth_oidc.py` retained the positive supplied-verifier form-body assertion and removed only the `code_verifier=None` omission block. The R2 auth service and route code were not changed in R3.
- **R3 focused test:** The first unquoted `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py` attempt from `backend/` exited 127 before tests because the shell parsed the Windows path separators. The same listed test command with the executable path quoted then exited 0: `'.venv\Scripts\python.exe' -m pytest -q tests/test_auth_oidc.py` (CWD `backend/`), `16 passed, 1 warning in 2.59s`.
- **R3 Ruff check:** `'.venv\Scripts\ruff.exe' check . ../dev` (CWD `backend/`), exit 0, `All checks passed!`.
- **R3 Ruff format check:** `'.venv\Scripts\ruff.exe' format --check app/auth/oidc.py app/auth/routes.py tests/test_auth_oidc.py` (CWD `backend/`), exit 0, `3 files already formatted`.
- **R3 root diff check:** `git diff --check` (repository root), exit 0, empty output.
- **Historical full suite:** R2 run 112, `.venv\Scripts\python.exe -m pytest -q` (CWD `backend/`), exit 0, `153 passed, 6 skipped, 1 warning in 12.06s`. R3 did not rerun it.
- **Correction to Section 7 wording:** The phrase “pre-existing trailing whitespace” is inaccurate. The exit 2 was caused by a CRLF line ending on the coordinator's own appended `.team/ledger.md:539` entry in an LF file. The coordinator normalized that line ending only; the exact root `git diff --check` subsequently exited 0. The Worker did not edit the ledger.
- The R2 transcript was not available through `hermes kanban log`; Section 7 records the captured deviations, but exact outputs for every intermediate invocation could not be recovered and are NOT_VERIFIED. The final prescribed R2 checks and the R3 checks are recorded above in their exact CWDs and with outcomes.
