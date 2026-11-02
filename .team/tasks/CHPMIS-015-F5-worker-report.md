# CHPMIS-015-F5 Worker Implementation Report

- **Task ID:** CHPMIS-015-F5 (Kanban task `t_779b041f`)
- **Role:** Hermes Backend Worker (implementation)
- **Status:** IMPLEMENTATION COMPLETE / READY FOR INDEPENDENT REVIEW
- **Parent Task:** CHPMIS-015 system-admin approval transaction
- **Requirement Traceability:** `.team/tasks/CHPMIS-015-F5-canonical-decision-authority.md`, mission §4B, approved CHPMIS-015 HG2 and decision-time authority criteria.
- **Prompt Template Trace:**
  - Real template: prompts.chat **Feature coding template**, author Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
  - Modernized task-specific adaptation: "Act as the CHPMIS-015 backend authorization Worker. Follow HG2 and the CHPMIS-015 transaction contract. Add synthetic RED regressions proving that legacy display-value rows cannot authorize a requester or approver at decision time, then make the smallest route-only correction. Preserve canonical-role behavior, bootstrap detection of legacy rows, F4 freshness checks, transaction/session/request invariants, and existing public contracts. Do not change schema, convert legacy rows, or widen policy. Modify only the allowlist, run only assigned checks, record exact outputs/exits, and request independent review; do not self-approve or commit."

---

## 1. Scope and File Compliance

Worker modified only the allowlisted product and test files:
1. `backend/app/auth/routes.py`:
   - Narrowed approver decision-time freshness check (`approver_role`) from `UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"])` to canonical `UserRole.role == Role.SYSTEM_ADMIN.value`.
   - Narrowed requester decision-time freshness check (`requester_role`) from `UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"])` to canonical `UserRole.role == Role.SYSTEM_ADMIN.value`.
   - Preserved `existing_grant` target user duplicate check detecting both canonical and legacy display-value rows to prevent unsafe duplicate admin creation.
2. `backend/tests/test_auth_remediation.py`:
   - Imported `BootstrapError` from `app.auth.bootstrap_admins`.
   - Added synthetic regression tests under `-k legacy_role`:
     1. `test_legacy_role_requester_cannot_authorize_approval`: Canonical requester creates request, loses canonical role and receives only legacy `"System Admin"` row. Canonical approver attempts approval; rejected with 403 `"Requester is no longer an active System Admin"`. Request remains pending, target receives no role, target session is not revoked.
     2. `test_legacy_role_approver_cannot_authorize_approval`:
        - Case 2A: Approver with only legacy `"System Admin"` row attempts approval -> 403.
        - Case 2B: Approver validates session with canonical role, but at decision time transitions to legacy-only row -> decision transaction rejects with 403 `"Approver must be an active System Admin"`. Request remains pending, target receives no role, target session is not revoked.
     3. `test_legacy_role_canonical_requester_and_approver_succeed_under_hg2`: Canonical requester and canonical approver succeed under existing HG2 policy (200 OK, approved status, target receives canonical role, target session revoked).
     4. `test_legacy_role_blocks_bootstrap_guard`: Bootstrap duplicate guard continues to detect legacy `"System Admin"` row and blocks bootstrap with `BootstrapError("System Admin already exists")`.
3. `.team/tasks/CHPMIS-015-F5-worker-report.md`:
   - Authored this worker report.

No schema changes, migrations, role conversions, bootstrap-policy changes, new privileges, session policy changes, dual-control changes, real identities, production/staging changes, or git commits were made.

---

## 2. Hypothesis and Root Cause Analysis

- **Hypothesis:** In `backend/app/auth/routes.py:292` and `backend/app/auth/routes.py:311`, the decision transaction used `UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"])`. Consequently, if a requester or approver lost their canonical `system_admin` role and held only a legacy display-value `"System Admin"` row, the transaction mistakenly treated them as authorized.
- **Root Cause Confirmed:**
  - When running `pytest tests/test_auth_remediation.py -k legacy_role` prior to route modification:
    - `test_legacy_role_requester_cannot_authorize_approval` failed: `assert 200 == 403` (legacy-holding requester permitted approval).
    - `test_legacy_role_approver_cannot_authorize_approval` failed: `assert 200 == 403` (legacy-holding approver permitted approval at decision time).
- **Remediation:**
  - Modified only the allowlist in `backend/app/auth/routes.py`:
    - `approver_role`: `UserRole.role == Role.SYSTEM_ADMIN.value`
    - `requester_role`: `UserRole.role == Role.SYSTEM_ADMIN.value`
  - All four regressions immediately turned GREEN.

---

## 3. TDD RED/GREEN Evidence

### RED Evidence (Before Route Modification)

```
$ .venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py -k legacy_role
FF..                                                                     [100%]
================================== FAILURES ===================================
____________ test_legacy_role_requester_cannot_authorize_approval _____________
...
>           assert resp.status_code == 403
E           assert 200 == 403
E            +  where 200 = <Response [200 OK]>.status_code
tests\test_auth_remediation.py:1015: AssertionError
_____________ test_legacy_role_approver_cannot_authorize_approval _____________
...
>           assert resp.status_code == 403
E           assert 200 == 403
E            +  where 200 = <Response [200 OK]>.status_code
tests\test_auth_remediation.py:1176: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_auth_remediation.py::test_legacy_role_requester_cannot_authorize_approval
FAILED tests/test_auth_remediation.py::test_legacy_role_approver_cannot_authorize_approval
2 failed, 2 passed, 8 deselected, 1 warning in 1.54s
Exit code: 1
```

### GREEN Evidence (After Route Modification)

```
$ .venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py -k legacy_role
....                                                                     [100%]
4 passed, 8 deselected, 1 warning in 1.23s
Exit code: 0
```

---

## 4. Verification Commands and Exit Codes

All verification commands executed from `backend/` and repository root:

1. **Focused legacy role test:**
   - Command: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py -k legacy_role`
   - Output: `.... [100%] 4 passed, 8 deselected, 1 warning in 1.23s`
   - Exit code: `0`

2. **Remediation test module:**
   - Command: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py`
   - Output: `............ [100%] 12 passed, 1 warning in 1.92s`
   - Exit code: `0`

3. **Full backend test suite:**
   - Command: `.venv\Scripts\python.exe -m pytest -q`
   - Output: `145 passed, 4 skipped, 1 warning in 8.60s`
   - Exit code: `0`
   - *Note on PostgreSQL skip:* 4 PostgreSQL integration tests skipped because `TEST_DATABASE_URL` is unset in this environment. No PostgreSQL evidence is claimed from SQLite.

4. **Ruff lint check:**
   - Command: `.venv\Scripts\ruff.exe check app/auth/routes.py tests/test_auth_remediation.py`
   - Output: `All checks passed!`
   - Exit code: `0`

5. **Ruff format check:**
   - Command: `.venv\Scripts\ruff.exe format --check app/auth/routes.py tests/test_auth_remediation.py`
   - Output: `2 files already formatted`
   - Exit code: `0`

6. **Git diff whitespace/cleanliness check:**
   - Command: `git diff --check -- backend/app/auth/routes.py backend/tests/test_auth_remediation.py .team/tasks/CHPMIS-015-F5-worker-report.md`
   - Output: *(clean, empty)*
   - Exit code: `0`

---

## 5. Handoff

Implementation DoD satisfied:
- Required synthetic RED/GREEN regressions pass.
- Existing requester/approver transaction and bootstrap duplicate guard are preserved.
- Ready for OpenCode read-only checks and separate Hermes Reviewer assessment.
