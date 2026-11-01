# CHPMIS-017-F1 Worker Implementation Report

- **Task ID:** CHPMIS-017-F1 (Kanban task `t_611c0336`)
- **Role:** Hermes Worker (implementation)
- **Status:** IMPLEMENTATION COMPLETE / READY FOR INDEPENDENT REVIEW
- **Parent Task:** CHPMIS-017 endpoint authorization matrix
- **Requirement Traceability:** `.team/tasks/CHPMIS-017-F1-missing-project-role.md`, `docs/security/SECURITY_MODEL.md`, `docs/product/USER_ROLES.md`, `CHPMIS-017`.
- **Prompt Template Trace:**
  - Real template: prompts.chat **Feature coding template**, author Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
  - Modernized task-specific adaptation: "Act as the bounded CHPMIS authorization Worker; inspect before editing, reproduce the missing-role fail-open condition with a failing test, implement the smallest deny-by-default correction consistent with the approved global/project-role intersection, preserve valid behavior and dirty work, run only assigned verification, record exact evidence and request independent review. Do not broaden role permissions."

---

## 1. Scope and File Compliance

Worker modified only the three allowlisted files:
1. `backend/app/auth/policy.py`:
   - Enforced fail-closed behavior for unresolved task parents: when `context.task_id` is provided but parent project cannot be resolved (`res.get_project_for_task(task_id)` is `None`), authorization immediately returns `False`.
   - Corrected project-role enforcement at line 193: when `project_id is not None`, explicit project assignment (`is_assigned_to_project`) and a non-null `project_role` are strictly required (`if not is_assigned_to_project or project_role is None: return False`).
   - Evaluated `proj_role_str` via `_is_role_permitted()` against the requested action so that missing, invalid, or unpermitted project roles fail closed, preserving the intersection requirement.
   - Preserved global project creation semantics: `Action.PROJECT_CREATE` without project scope remains permitted for global `PROJECT_MANAGER`.
2. `backend/tests/test_auth_policy.py`:
   - Updated `MockProjectScopeResolver` to store `self.project_roles: dict[tuple[str, str], str]` and implement `get_user_project_role(user_id, project_id)`.
   - Supplied explicit valid project roles to existing unit test resolver fixtures (`test_project_manager_scoped_to_assigned_project`, `test_member_permissions_and_own_task_update`, `test_auditor_permissions`, `test_multi_role_intersection_policy_ac17`) consistent with their intended scenarios.
   - Added focused regression test `test_missing_project_role_fail_closed` covering:
     1. Missing project role under active project assignment -> fails closed (`assert False`).
     2. Invalid project role -> fails closed (`assert False`).
     3. Positive and negative intersections between global and project roles (e.g. global PM + project PM passes; global PM + project Member fails for `project:manage`; global Member + project PM fails for `project:manage`).
     4. Unresolved task parent -> fails closed (`assert False`).
     5. Global project creation semantics preserved (PM allowed, Member denied).
3. `.team/tasks/CHPMIS-017-F1-worker-report.md`:
   - Authored this worker report.

No schema, migration, configuration, or unrelated files were modified. All preexisting dirty working tree modifications across 20 other files and 34 untracked files were preserved untouched.

---

## 2. Hypothesis and Root Cause Analysis

- **Hypothesis:** At `backend/app/auth/policy.py:193`, project-role enforcement previously guarded execution with `if project_id is not None and project_role is not None:`. If a resolver reported explicit project assignment (`is_user_assigned_to_project == True`) but returned `None` for `get_user_project_role` (or lacked a concrete implementation), the second intersection step was bypassed completely, granting access based solely on the global role.
- **Root Cause Confirmed:** In `test_missing_project_role_fail_closed`, calling `authorize()` with `project_id="p1"`, explicit assignment in `MockProjectScopeResolver`, but no project role returned `True` (failed open).
- **Remediation:** Changed guard to:
  ```python
  if project_id is not None:
      if not is_assigned_to_project or project_role is None:
          return False
      proj_role_str = str(project_role.value if isinstance(project_role, Role) else project_role)
      if not _is_role_permitted(
          proj_role_str, act, principal, project_id, task_id, is_assigned_to_project, res
      ):
          return False
  ```
  Additionally, for task parent resolution:
  ```python
  if project_id is None and task_id is not None:
      project_id = res.get_project_for_task(task_id)
      if project_id is None:
          return False
  ```

---

## 3. TDD RED/GREEN Evidence

### RED Evidence (Before Implementation)

**Command:**
```bash
./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k missing_project_role
```

**Output:**
```
F                                                                        [100%]
================================== FAILURES ===================================
____________________ test_missing_project_role_fail_closed ____________________

    def test_missing_project_role_fail_closed():
        pm = Principal(
            id="pm1", sub="spm", email="pm@test.com", name="PM 1", roles=[Role.PROJECT_MANAGER]
        )
        member = Principal(
            id="m1", sub="sm1", email="m1@test.com", name="Member 1", roles=[Role.MEMBER]
        )
        resolver = MockProjectScopeResolver()
        resolver.project_assignments.add(("pm1", "p1"))
        resolver.project_assignments.add(("m1", "p1"))

        # 1. Assignment true with missing project role: fails closed
>       assert authorize(pm, Action.PROJECT_READ, ResourceContext(project_id="p1"), resolver) is False
E       AssertionError: assert True is False
E        +  where True = authorize(Principal(id='pm1', sub='spm', email='pm@test.com', name='PM 1', roles=[<Role.PROJECT_MANAGER: 'project_manager'>], department=None, is_active=True), <Action.PROJECT_READ: 'project:read'>, ResourceContext(project_id='p1', task_id=None, department=None, project_role=None), <test_auth_policy.MockProjectScopeResolver object at 0x0000027E74DCFB60>)
E        +    where <Action.PROJECT_READ: 'project:read'> = Action.PROJECT_READ
E        +    and   ResourceContext(project_id='p1', task_id=None, department=None, project_role=None) = ResourceContext(project_id='p1')

backend\tests\test_auth_policy.py:587: AssertionError
=========================== short test summary info ===========================
FAILED backend\tests\test_auth_policy.py::test_missing_project_role_fail_closed
1 failed, 11 deselected in 0.18s
```
**Exit Code:** `1`

---

### GREEN Evidence (After Implementation)

**Command:**
```bash
./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k missing_project_role
```

**Output:**
```
.                                                                        [100%]
1 passed, 11 deselected in 0.13s
```
**Exit Code:** `0`

---

## 4. Full Assigned Verification Suite

### Check 1: Focused regression test (RED and GREEN)
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k missing_project_role`
- **Output:**
  ```
  .                                                                        [100%]
  1 passed, 11 deselected in 0.13s
  ```
- **Exit code:** `0`

### Check 2: Auth policy test suite
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
- **Output:**
  ```
  ............                                                             [100%]
  ============================== warnings summary ===============================
  tests/test_auth_policy.py::test_system_admin_api_endpoints
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  12 passed, 1 warning in 1.20s
  ```
- **Exit code:** `0`

### Check 3: Project, task workflow, and dashboard/audit integration tests
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
- **Output:**
  ```
  ............................                                             [100%]
  ============================== warnings summary ===============================
  backend\.venv\Lib\site-packages\fastapi\testclient.py:1
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  28 passed, 1 warning in 4.45s
  ```
- **Exit code:** `0`

### Check 4: Full backend test suite
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests`
- **Output:**
  ```
  ........................................................................ [ 51%]
  ...................................ss..............................      [100%]
  ============================== warnings summary ===============================
  backend\.venv\Lib\site-packages\fastapi\testclient.py:1
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  137 passed, 2 skipped, 1 warning in 7.12s
  ```
- **Exit code:** `0`

### Check 5: Scoped Ruff linter check
- **Command:** `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/auth/policy.py backend/tests/test_auth_policy.py`
- **Output:**
  ```
  All checks passed!
  ```
- **Exit code:** `0`

### Check 6: Scoped Ruff format check
- **Command:** `./backend/.venv/Scripts/ruff.exe format --check backend/app/auth/policy.py backend/tests/test_auth_policy.py`
- **Output:**
  ```
  2 files already formatted
  ```
- **Exit code:** `0`

### Check 7: Git diff check (whitespace/patch sanity)
- **Command:** `git diff --check`
- **Output:** *(empty)*
- **Exit code:** `0`

---

## 5. Summary of Deliverables and Follow-Up

- **What Changed:**
  - `backend/app/auth/policy.py`: fail-closed guard when `project_role is None` or `not is_assigned_to_project` on project-scoped resources; fail-closed guard for unresolved task parents.
  - `backend/tests/test_auth_policy.py`: implemented `get_user_project_role` in `MockProjectScopeResolver`, updated unit test fixtures with explicit role data, added `test_missing_project_role_fail_closed`.
  - `.team/tasks/CHPMIS-017-F1-worker-report.md`: authored implementation evidence report.
- **What Was Verified:**
  - 7/7 assigned checks exit 0 with clean evidence.
  - Missing project role fails closed.
  - Invalid project role fails closed.
  - Positive and negative global/project role intersections confirmed.
  - Unresolved task parents fail closed.
  - Global project creation semantics preserved.
  - All existing backend tests (137 passed, 2 skipped) remain green.
- **What Remains:**
  - Fresh independent review by Reviewer role.
  - Coordinator ledger and task updates.
