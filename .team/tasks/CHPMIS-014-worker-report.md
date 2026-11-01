# CHPMIS-014 Worker Implementation Report

- **Task ID:** CHPMIS-014 (Kanban task `t_8994c6db`)
- **Role:** Hermes Worker (sole product/test-code writer)
- **Status:** IMPLEMENTATION COMPLETE / AWAITING INDEPENDENT TESTER & REVIEWER
- **Trace:** Mission A2; approved Human Gate 2; finding A2-01 in `docs/audit/AUDIT_REMEDIATION.md`
- **Prompt Template:** Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa` (adapted to Python/FastAPI/SQLAlchemy, TDD, HTTP regression, synthetic-only fixtures, exact verification)

---

## 1. Scope and File Compliance

Worker modified or authored only the allowlisted files:
1. `backend/app/auth/bootstrap_admins.py`:
   - Imported canonical `Role` from `app.auth.policy`.
   - Updated zero-admin precondition check to block both canonical `Role.SYSTEM_ADMIN.value` (`system_admin`) and legacy display-value rows (`System Admin`):
     `db.query(UserRole).filter(UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"])).count()`
   - Updated role grant creation during atomic bootstrap transaction to use canonical `Role.SYSTEM_ADMIN.value` (`system_admin`) instead of display string `"System Admin"`.
   - Preserved legacy rows without conversion, elevation, or normalization.
2. `backend/tests/test_auth_remediation.py`:
   - Added synthetic Ed25519 keypair and payload signing fixtures.
   - Added HTTP integration regression `test_bootstrap_admin_session_recognized_by_protected_endpoint`:
     Uses synthetic keys, calls `bootstrap_initial_admins`, creates a session for the bootstrapped admin, validates canonical `Role.SYSTEM_ADMIN.value` (`system_admin`) in session roles, and performs HTTP `GET /api/v1/auth/roles/system-admin/requests` via `TestClient(app)` asserting HTTP 200 and successful response payload.
3. `backend/tests/test_admin_bootstrap.py`:
   - Updated `test_bootstrap_success` to verify persisted role matches `Role.SYSTEM_ADMIN.value` (`system_admin`).
   - Retained test for legacy display-value rows blocking bootstrap: `test_bootstrap_rejects_preexisting_legacy_display_value_admin`.
   - Added test for canonical role blocking bootstrap: `test_bootstrap_rejects_preexisting_canonical_admin`.
   - Updated atomic rollback test `test_bootstrap_atomic_rollback_on_fault_injection` to verify neither canonical nor legacy admin role rows persist after rollback.
4. `.team/tasks/CHPMIS-014-worker-report.md`:
   - Authored this report.

No files outside this list were changed. No migrations, ordinary grant/revoke semantics, auth policy, trust-source behavior, `.env`, or Compose were altered. No commits were made.

---

## 2. Test-Driven Development (TDD) Evidence

### Step 1 & 2: RED Phase (Integration Regression)

Authored HTTP integration regression `test_bootstrap_admin_session_recognized_by_protected_endpoint` in `backend/tests/test_auth_remediation.py` before editing production code.

**Command executed:**
```
cd backend && .venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint -vv
```

**Output (RED):**
```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.2.0, pluggy-1.7.0 -- D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 1 item

tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint FAILED [100%]

================================== FAILURES ===================================
________ test_bootstrap_admin_session_recognized_by_protected_endpoint ________

    def test_bootstrap_admin_session_recognized_by_protected_endpoint():
...
            # Create and validate session for bootstrapped admin 1
            sess = create_session(db, u1.id, settings)
            _, _, roles = validate_session(db, sess.id, settings)
>           assert "system_admin" in roles
E           AssertionError: assert 'system_admin' in ['System Admin']

tests\test_auth_remediation.py:419: AssertionError
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint
======================== 1 failed, 1 warning in 1.37s =========================
```
**Exit code:** `1`

The RED output reproduces finding A2-01: bootstrap persisted `'System Admin'`, causing session validation to return stored strings that did not match canonical policy key `system_admin`, which would subsequently return HTTP 403 Forbidden on protected System Admin endpoints.

### Step 3 & 4: GREEN Phase (Implementation & Test Coverage)

Applied minimal changes to `backend/app/auth/bootstrap_admins.py` and test updates to `backend/tests/test_admin_bootstrap.py`.

**Command executed:**
```
cd backend && .venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint -vv
```

**Output (GREEN):**
```
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.2.0, pluggy-1.7.0 -- D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 1 item

tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint PASSED [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\\.venv\\Lib\\site-packages\\fastapi\\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 1 passed, 1 warning in 1.07s =========================
```
**Exit code:** `0`

---

## 3. Verification Commands and Exact Results

### Command 1: Focused regression & bootstrap tests
- **Directory:** `backend/`
- **Command:** `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py tests/test_auth_remediation.py`
- **Output:**
  ```
  ..................                                                       [100%]
  ============================== warnings summary ===============================
  .venv\Lib\site-packages\fastapi\testclient.py:1
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  18 passed, 1 warning in 1.48s
  ```
- **Exit code:** `0`
- **Counts:** 18 passed, 0 failed, 1 warning

### Command 2: Full backend suite
- **Directory:** `backend/`
- **Command:** `.venv\Scripts\python.exe -m pytest -q`
- **Output:**
  ```
  ........................................................................ [ 71%]
  s............................                                            [100%]
  ============================== warnings summary ===============================
  .venv\Lib\site-packages\fastapi\testclient.py:1
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  100 passed, 1 skipped, 1 warning in 5.06s
  ```
- **Exit code:** `0`
- **Counts:** 100 passed, 1 skipped (test_postgresql.py skipped when TEST_DATABASE_URL unset), 1 warning

### Command 3: Ruff lint check
- **Directory:** `backend/`
- **Command:** `.venv\Scripts\ruff.exe check . ../dev`
- **Output:**
  ```
  All checks passed!
  ```
- **Exit code:** `0`

### Command 4: Ruff formatting check on scoped files
- **Directory:** `backend/`
- **Command:** `.venv\Scripts\ruff.exe format --check app/auth/bootstrap_admins.py tests/test_admin_bootstrap.py tests/test_auth_remediation.py`
- **Output:**
  ```
  3 files already formatted
  ```
- **Exit code:** `0`

### Command 5: Git diff check
- **Directory:** Repository root (`D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`)
- **Command:** `git diff --check`
- **Output:** *(empty — no whitespace, formatting, or merge conflict marker issues)*
- **Exit code:** `0`

---

## 4. Policy, Boundaries, and Limitations

1. **Database Dialect:**
   - Verification executed against SQLite via `StaticPool` in-memory database as configured in test fixtures.
   - `test_postgresql.py` skipped because `TEST_DATABASE_URL` is unset; no PostgreSQL behavior inferred from SQLite evidence.
2. **Legacy Row Policy:**
   - Precondition check fails closed (`BootstrapError: System Admin already exists; bootstrap is only permitted when zero System Admins exist`) if either canonical `system_admin` or legacy display-value `System Admin` rows exist.
   - No rows are updated, migrated, or elevated. Legacy display rows remain inert.
3. **Key-Source Questions:**
   - Unresolved HKLM trust-source / production key custody questions remain unchanged and are not addressed in this task (scoped to CHPMIS-016). All keys used in tests are test-scoped synthetic keys.
4. **Git Commit Status:**
   - Worker has not staged or committed any changes per instructions.

---

## 5. Recommended Commit Message

```
fix(auth): use canonical role key in admin bootstrap and guard legacy rows

- Use Role.SYSTEM_ADMIN.value ('system_admin') when inserting bootstrapped UserRole records
- Update zero-admin precondition check to block both canonical ('system_admin') and legacy ('System Admin') rows
- Add HTTP integration regression proving bootstrapped session accesses protected System Admin endpoint
- Add unit tests proving canonical and legacy admin rows block bootstrap
- Trace: CHPMIS-014, Mission A2, finding A2-01
```
