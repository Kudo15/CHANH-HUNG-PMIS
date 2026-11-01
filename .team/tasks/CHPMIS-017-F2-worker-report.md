# CHPMIS-017-F2 Worker Implementation Report

- **Task ID:** CHPMIS-017-F2 (Kanban task `t_1ef0b522`)
- **Role:** Hermes Worker (implementation)
- **Status:** IMPLEMENTATION COMPLETE / READY FOR INDEPENDENT REVIEW
- **Parent Task:** CHPMIS-017 endpoint authorization matrix
- **Requirement Traceability:** `.team/tasks/CHPMIS-017-F2-task-context-proposal.md`, `backend/app/auth/policy.py`, `docs/security/SECURITY_MODEL.md`, `CHPMIS-017`.
- **Prompt Template Trace:**
  - Real template: prompts.chat **Feature coding template**, author Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
  - Modernized task-specific adaptation: "Act as the bounded CHPMIS authorization Worker; inspect the approved matrix, shared helper and actual callers before editing; demonstrate the mismatched task/project case with a failing synthetic regression, implement the smallest fail-closed correction, preserve legitimate matching and task-only contexts plus existing dirty work, run the exact listed checks, record outputs, exit codes and deviations, and request independent review."

---

## 1. Scope and File Compliance

Worker modified only the three allowlisted files:
1. `backend/app/auth/policy.py`:
   - Updated lines 172-178 in `authorize()` so that whenever `task_id is not None`, the task's parent project is resolved via `res.get_project_for_task(task_id)`.
   - If the task parent cannot be resolved (`task_project_id is None`), authorization fails closed (`return False`).
   - If a caller supplies both `project_id` and `task_id`, and `project_id != task_project_id`, authorization fails closed (`return False`).
   - If `project_id is None` and `task_id is not None`, `project_id` is set to `task_project_id` (task-only resolution preserved).
   - Valid matching contexts (`project_id == task_project_id`) proceed to evaluate permissions under the matching project scope.
2. `backend/tests/test_auth_policy.py`:
   - Added `test_task_project_mismatch_fail_closed` covering:
     1. Mismatch between caller-supplied `project_id` and the task's actual parent project fails closed for both PM (`TASK_READ`) and Member (`TASK_READ`, `TASK_UPDATE`).
     2. Unresolvable task parent fails closed even when caller supplies an authorized `project_id`.
     3. Valid matching supplied `project_id` and `task_id` succeed where policy permits.
     4. Task-only context resolution (`project_id=None`, `task_id` supplied) is preserved.
3. `.team/tasks/CHPMIS-017-F2-worker-report.md`:
   - Authored this implementation evidence report.

No schema, migration, configuration, or other files were modified. All preexisting dirty working tree modifications across 22 other files and 38 untracked files were preserved untouched.

---

## 2. Hypothesis and Root Cause Analysis

- **Hypothesis:** At `backend/app/auth/policy.py:172`, the helper previously checked `if project_id is None and task_id is not None:`. When a direct caller supplied both `context.project_id = "proj_a"` and `context.task_id = "task_b"` (where `task_b` belongs to `proj_b`), `project_id` was already non-null, so `res.get_project_for_task(task_id)` was never invoked. If the actor had authorization on `proj_a`, `authorize()` would evaluate permissions against `proj_a` and return `True`, failing to check or enforce that `task_b` actually belonged to `proj_a`.
- **Root Cause Confirmed:** In `test_task_project_mismatch_fail_closed`, calling `authorize()` with `ResourceContext(project_id="proj_a", task_id="task_b")` returned `True` (failed open).
- **Remediation:** Changed resolution block in `backend/app/auth/policy.py` to:
  ```python
  if task_id is not None:
      task_project_id = res.get_project_for_task(task_id)
      if task_project_id is None:
          return False
      if project_id is not None and project_id != task_project_id:
          return False
      project_id = task_project_id
  ```

---

## 3. TDD RED/GREEN Evidence

### RED Evidence (Before Implementation)

**Command:**
```bash
./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k task_project_mismatch
```

**Output:**
```
F                                                                        [100%]
================================== FAILURES ===================================
___________________ test_task_project_mismatch_fail_closed ____________________

    def test_task_project_mismatch_fail_closed():
        pm = Principal(
            id="pm1", sub="spm", email="pm@test.com", name="PM 1", roles=[Role.PROJECT_MANAGER]
        )
        member = Principal(
            id="m1", sub="sm1", email="m1@test.com", name="Member 1", roles=[Role.MEMBER]
        )
        resolver = MockProjectScopeResolver()
        resolver.project_assignments.add(("pm1", "proj_a"))
        resolver.project_roles[("pm1", "proj_a")] = Role.PROJECT_MANAGER.value
        resolver.project_assignments.add(("m1", "proj_a"))
        resolver.project_roles[("m1", "proj_a")] = Role.MEMBER.value

        # proj_a has task_a; proj_b has task_b
        resolver.task_projects["task_a"] = "proj_a"
        resolver.task_projects["task_b"] = "proj_b"
        resolver.task_assignments.add(("m1", "task_a"))

        # 1. Mismatch between supplied project_id and task's actual parent project: fails closed
        # Caller supplies proj_a (where pm1 has access) but task_b (which belongs to proj_b)
        ctx_mismatch_pm = ResourceContext(project_id="proj_a", task_id="task_b")
>       assert authorize(pm, Action.TASK_READ, ctx_mismatch_pm, resolver) is False
E       AssertionError: assert True is False
E        +  where True = authorize(Principal(id='pm1', sub='spm', email='pm@test.com', name='PM 1', roles=[<Role.PROJECT_MANAGER: 'project_manager'>], department=None, is_active=True), <Action.TASK_READ: 'task:read'>, ResourceContext(project_id='proj_a', task_id='task_b', department=None, project_role=None), <test_auth_policy.MockProjectScopeResolver object at 0x000001AC4E71FB60>)
E        +    where <Action.TASK_READ: 'task:read'> = Action.TASK_READ

backend\tests\test_auth_policy.py:658: AssertionError
=========================== short test summary info ===========================
FAILED backend\tests\test_auth_policy.py::test_task_project_mismatch_fail_closed
1 failed, 12 deselected in 0.26s
```
**Exit Code:** `1`

---

### GREEN Evidence (After Implementation)

**Command:**
```bash
./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k task_project_mismatch
```

**Output:**
```
.                                                                        [100%]
1 passed, 12 deselected in 0.02s
```
**Exit Code:** `0`

---

## 4. Full Assigned Verification Suite

### Check 1: Focused regression test (RED and GREEN)
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k task_project_mismatch`
- **Output:**
  ```
  .                                                                        [100%]
  1 passed, 12 deselected in 0.02s
  ```
- **Exit code:** `0`

### Check 2: Auth policy test suite
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
- **Output:**
  ```
  .............                                                            [100%]
  ============================== warnings summary ===============================
  tests/test_auth_policy.py::test_system_admin_api_endpoints
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  13 passed, 1 warning in 3.41s
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
  28 passed, 1 warning in 5.34s
  ```
- **Exit code:** `0`

### Check 4: Full backend test suite
- **Command:** `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests`
- **Output:**
  ```
  ........................................................................ [ 51%]
  ....................................ss..............................     [100%]
  ============================== warnings summary ===============================
  backend\.venv\Lib\site-packages\fastapi\testclient.py:1
    D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
      from starlette.testclient import TestClient as TestClient  # noqa

  -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
  138 passed, 2 skipped, 1 warning in 8.11s
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
  - `backend/app/auth/policy.py`: fail-closed guard when `task_id` is supplied and its parent project cannot be resolved by the resolver (`task_project_id is None`) or when caller-supplied `project_id != task_project_id`.
  - `backend/tests/test_auth_policy.py`: added `test_task_project_mismatch_fail_closed` verifying fail-closed enforcement on mismatch, unresolvable task parent, valid matching contexts, and task-only resolution.
  - `.team/tasks/CHPMIS-017-F2-worker-report.md`: authored implementation evidence report.
- **What Was Verified:**
  - 7/7 assigned checks exit 0 with clean evidence.
  - Mismatched task and project identifiers fail closed.
  - Unresolved task parents fail closed.
  - Matching task and project identifiers remain permitted where policy allows.
  - Task-only resolution remains permitted where policy allows.
  - Global project creation semantics preserved.
  - All existing backend tests (138 passed, 2 skipped) remain green.
  - Scoped Ruff check and format check passed cleanly on allowlisted files. (Repository-wide Ruff passes are not claimed; previously documented 14 unrelated Ruff findings remain).
  - Preexisting dirty work preserved.
- **What Remains:**
  - Fresh independent review by Reviewer role.
  - Coordinator ledger and task updates.
