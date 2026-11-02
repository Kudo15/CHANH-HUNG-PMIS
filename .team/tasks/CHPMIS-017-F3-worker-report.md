# CHPMIS-017-F3 Worker Implementation Report

- **Task ID:** CHPMIS-017-F3 (Kanban task `t_e4f5224f`)
- **Role:** Hermes Backend Worker (implementation)
- **Status:** IMPLEMENTATION COMPLETE / READY FOR INDEPENDENT REVIEW
- **Parent Task:** CHPMIS-017 endpoint authorization matrix
- **Requirement Traceability:** `.team/tasks/CHPMIS-017-F3-empty-global-roles.md`, mission §4A, approved CHPMIS-017 deny-by-default intersection contract, A4-01/A4-02.
- **Prompt Template Trace:**
  - Real template: prompts.chat **Feature coding template**, author Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
  - Modernized task-specific adaptation: "Act as the CHPMIS-017 backend authorization Worker. Inspect the approved intersection contract and all relevant HTTP/service callsites. First add a synthetic RED regression for an active user with membership and no global roles; then make the smallest server-side correction so list/dashboard and related reads fail closed. Preserve existing `authorize(roles=[])` denial, intersection, endpoint contracts, and all unrelated work. Do not infer semantics for `actor_roles=None`; report affected callsites and stop if a policy choice is required. Use only the listed files, run only the listed checks, report exact evidence and request independent review; do not self-approve or commit."

---

## 1. Scope and File Compliance

Worker modified only allowlisted product and test files:
1. `backend/app/projects/routes.py`:
   - In `list_projects`, added early fail-closed guard `if not roles: return []`. When an authenticated user has zero global roles (`roles == []`), the endpoint immediately returns an empty list `[]`, disclosing no project records even if explicit `ProjectMember` records exist.
2. `backend/app/projects/service.py`:
   - In `get_dashboard_summary`, under `if actor_roles is not None:`, added early fail-closed check `if not actor_roles: return empty_resp`. When an authenticated user has zero global roles, the service immediately returns an empty summary response (`projects=[]`, `total_projects=0`, `total_tasks=0`, `total_overdue_tasks=0`), disclosing no business aggregates.
   - Preserved `actor_roles=None` semantics untouched for unauthenticated/unscoped internal callsites.
3. `backend/tests/test_projects.py`:
   - Added synthetic regression test `test_empty_global_roles_deny_project_reads_and_detail_endpoints` covering:
     1. Authenticated user with project membership but zero `UserRole` rows gets `[]` on `GET /api/v1/projects` and `404` on `GET /api/v1/projects/{project_id}` and `GET /api/v1/projects/{project_id}/members`.
     2. Mutation attempts (`POST /api/v1/projects`, `POST /api/v1/projects/{id}/members`, `POST /api/v1/projects/{id}/archive`) return `403`.
     3. Role revocation: active member with project membership can initially list and view project; after revoking their final global role in the DB, subsequent list calls return `[]` and detail/member calls return `404`.
4. `backend/tests/test_dashboard_audit.py`:
   - Added synthetic regression test `test_empty_global_roles_deny_dashboard_and_audit_reads` covering:
     1. Authenticated user with project membership but zero `UserRole` rows gets empty dashboard summary (`total_projects=0`, `total_tasks=0`, `projects=[]`) and `404` on `GET /api/v1/projects/{project_id}/audit-events`.
     2. Role revocation: active PM user can initially view dashboard counts and audit events; after revoking their final global role in DB, subsequent dashboard summary returns 0/empty and audit events return `404`.
5. `backend/tests/test_tasks_workflow.py`:
   - Added synthetic test `test_empty_global_roles_deny_task_endpoints` verifying that all task endpoints (`POST /api/v1/projects/{id}/tasks`, `GET /api/v1/projects/{id}/tasks`, `GET /api/v1/tasks/{id}`, `PATCH /api/v1/tasks/{id}/status`) fail closed (`403` or `404`) for users with zero global roles.
6. `.team/tasks/CHPMIS-017-F3-worker-report.md`:
   - Authored this worker report.

No schema, migrations, UI, external identity, deployment, or unrelated files were modified. Preexisting untracked files and working tree modifications were preserved untouched.

---

## 2. Hypothesis and Root Cause Analysis

- **Hypothesis:** In `backend/app/projects/routes.py:72` (`list_projects`) and `backend/app/projects/service.py:704` (`get_dashboard_summary`), global role intersection was evaluated via a loop `for r in roles:` (or `for r in actor_roles:`). When an authenticated user has zero global roles (`roles == []`), the loop executed zero times and did not deny. The execution then proceeded to query explicit project memberships from `ProjectMember`, disclosing project records in `list_projects` and project task counts in `get_dashboard_summary` despite the absence of any global roles.
- **Root Cause Confirmed:**
  - In `backend/tests/test_projects.py`, an active user with project membership but no global roles received `[ProjectRead(...)]` instead of `[]` (AssertionError: `assert [{'id': '...'}] == []`).
  - In `backend/tests/test_dashboard_audit.py`, an active user with project membership but no global roles received `total_projects: 1` instead of `0` (AssertionError: `assert 1 == 0`).
- **Remediation:**
  - In `list_projects`: added `if not roles: return []` before the role iteration.
  - In `get_dashboard_summary`: added `if not actor_roles: return empty_resp` under `if actor_roles is not None:`.
  - In detail, member, task, and audit endpoints: all routes rely on `authorize(principal, Action.XXX, ...)` (or service functions that call `authorize()`), where line 161 of `backend/app/auth/policy.py` (`if not principal.is_active or not principal.roles: return False`) already strictly denies empty global roles.

---

## 3. Callsite Audit for `actor_roles=None`

Per task instructions, audited all service functions taking optional `actor_roles: list[str] | None = None`:
- `archive_project(db, actor_id, project_id, correlation_id, actor_roles=None)`:
  - Route caller (`backend/app/projects/routes.py:185`): passes `actor_roles=roles`. When `roles=[]`, `authorize()` fails closed (`403`).
  - If `actor_roles is None`: internal callsites retain existing project-manager-only checks without global role intersection. Semantics preserved.
- `assign_project_member(db, actor_id, project_id, payload, correlation_id, actor_roles=None)`:
  - Route caller (`backend/app/projects/routes.py:216`): passes `actor_roles=roles`. When `roles=[]`, `authorize()` fails closed (`403`).
  - If `actor_roles is None`: semantics preserved.
- `create_task(db, actor_id, project_id, payload, correlation_id, actor_roles=None)`:
  - Route caller (`backend/app/projects/routes.py:276`): passes `actor_roles=roles`. When `roles=[]`, `authorize()` fails closed (`403`).
  - If `actor_roles is None`: semantics preserved.
- `transition_task_status(db, actor_id, task_id, target_status, correlation_id, actor_roles=None)`:
  - Route caller (`backend/app/projects/routes.py:358`): passes `actor_roles=roles`. When `roles=[]`, `authorize()` fails closed (`403`).
  - If `actor_roles is None`: semantics preserved.
- `get_dashboard_summary(db, user_id, as_of=None, actor_roles=None)`:
  - Route caller (`backend/app/projects/routes.py:379`): passes `actor_roles=roles`. When `roles=[]`, now returns `empty_resp`.
  - If `actor_roles is None`: internal/legacy callers retain unscoped membership aggregation without global role intersection. Semantics preserved.
- `list_project_audit_events(db, actor_id, project_id, limit, cursor, actor_roles=None)`:
  - Route caller (`backend/app/projects/routes.py:396`): passes `actor_roles=roles`. When `roles=[]`, `authorize()` fails closed (`404`).
  - If `actor_roles is None`: semantics preserved.

No unapproved changes or bypasses were added to `actor_roles=None` semantics.

---

## 4. TDD RED/GREEN Evidence

### RED Evidence (Before Server-Side Remediation)

1. `test_empty_global_roles_deny_project_reads_and_detail_endpoints` in `backend/tests/test_projects.py`:
```
./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py -k empty_global_roles
F                                                                        [100%]\r
================================== FAILURES ===================================\r
_______ test_empty_global_roles_deny_project_reads_and_detail_endpoints _______\r
...
    # GET /api/v1/projects must disclose no rows
    r_list = client.get("/api/v1/projects")
    assert r_list.status_code == 200
>   assert r_list.json() == []
E   AssertionError: assert [{'id': 'c2ea...pt-egr', ...}] == []
...
FAILED backend\tests\test_projects.py::test_empty_global_roles_deny_project_reads_and_detail_endpoints
1 failed, 8 deselected, 1 warning in 1.41s
Exit code: 1
```

2. `test_empty_global_roles_deny_dashboard_and_audit_reads` in `backend/tests/test_dashboard_audit.py`:
```
./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_dashboard_audit.py -k empty_global_roles
F                                                                        [100%]\r
================================== FAILURES ===================================\r
___________ test_empty_global_roles_deny_dashboard_and_audit_reads ____________\r
...
    # 1. User with zero global roles gets empty summary and denied audit read
    client.cookies.set(settings.session_cookie_name, s_empty.id)
    d_empty = client.get("/api/v1/dashboard/summary").json()
>   assert d_empty["total_projects"] == 0
E   assert 1 == 0
...
FAILED backend\tests\test_dashboard_audit.py::test_empty_global_roles_deny_dashboard_and_audit_reads
1 failed, 14 deselected, 1 warning in 1.57s
Exit code: 1
```

### GREEN Evidence (After Remediation)

All assigned verification commands were executed from repository root and recorded with exact outputs and exit codes:

1. Focused projects empty_global_roles test:
```
$ ./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py -k empty_global_roles
.                                                                        [100%]
1 passed, 8 deselected, 1 warning in 1.22s
Exit code: 0
```

2. Focused dashboard empty_global_roles test:
```
$ ./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_dashboard_audit.py -k empty_global_roles
.                                                                        [100%]
1 passed, 14 deselected, 1 warning in 1.18s
Exit code: 0
```

3. Full project, task, and dashboard audit test suites:
```
$ ./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py
...............................                                          [100%]
31 passed, 1 warning in 5.06s
Exit code: 0
```

4. Auth policy test suite:
```
$ ./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py
.............                                                            [100%]
13 passed, 1 warning in 1.28s
Exit code: 0
```

5. Ruff lint check:
```
$ ./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py
All checks passed!
Exit code: 0
```

6. Ruff format check:
```
$ ./backend/.venv/Scripts/ruff.exe format --check backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py
6 files already formatted
Exit code: 0
```

7. Git diff whitespace and boundary check:
```
$ git diff --check
(empty output)
Exit code: 0
```

---

## 5. Review Readiness and Next Steps

- Implementation and focused TDD are complete.
- All 7 verification commands pass with exit code 0.
- Handing off to independent OpenCode verifier for read-only verification and separate Hermes Reviewer.
