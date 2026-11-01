# Task Pack — CHPMIS-017 Endpoint Authorization Matrix

## Task ID, roles, status
- Task ID: CHPMIS-017
- Roles: Hermes Backend Worker → OpenCode read-only checks → independent Hermes Reviewer for source and security assessment
- Status: `COMPLETE for local scope` — F1 and F2 completed and independently reviewed; Worker full backend checks and Coordinator scoped Ruff/format checks passed. The 14 out-of-scope Ruff findings are tracked in `CHPMIS-017-L1`; remote CI, actual IdP and applicable live runtime limits remain NOT_VERIFIED.
- Coordinator owns this pack and evidence/ledger updates; only the Worker may edit product code.

## Context and approved contract
The next planned task is the endpoint matrix for audit findings A4-01/A4-02. `docs/security/SECURITY_MODEL.md`, `docs/product/USER_ROLES.md`, and CHPMIS-003 approve deny-by-default server authorization, explicit project membership, no department-only access, no implicit System Admin business-data access, Member task-state changes only for own assigned tasks, and Auditor access to audit history only for assigned projects. The audit plan also requires testing multi-role identities consistently.

Current review confirms project detail, member list, project task list/detail, and dashboard summary use any `ProjectMember` row as read authorization. Project audit history already checks project-scoped Project Manager/Auditor membership. Mutation services perform additional per-project role checks, but their routes and multi-role identity interaction need complete HTTP coverage.

## Objective
Enforce the approved role/action/project-scope contract consistently at every existing protected project/task/dashboard/audit HTTP endpoint and add positive and negative HTTP integration coverage for role, assignment, cross-project, department-only, System Admin, and task-assignee boundaries.

## Owner-selected multi-role policy
On 2026-11-01 the owner selected **intersection of all role permissions**: allow an action only when every applicable role permits it. For project-scoped endpoints, the action must also be allowed by the user's `ProjectMember.role` for that project, the user must be explicitly assigned to that project, and task-specific rules still apply. For project creation, all global `UserRole` grants must allow `PROJECT_CREATE`; there is no project membership scope yet. This is a deny-by-default rule and adds no business capability.

Examples required in HTTP coverage:
- System Admin + Project Manager: no business-data action, because System Admin does not permit one.
- Project Manager + Member: only overlapping read actions from the global grants; project assignment and task-specific policy further restrict access.
- Project Manager + Auditor: audit read can remain allowed when both global roles and the project membership permit it; non-audit actions are denied by Auditor.
- Member + Auditor: no business action is common to both role permission sets and therefore fails closed.
- Any combination without explicit project membership remains denied or returns the existing non-disclosing response.

## Endpoint matrix in scope
Test the actual HTTP routes below. Use synthetic identities, two projects, assigned/unassigned scopes, department-only matches, and task assignee/non-assignee cases.

| Endpoint | Project Manager in scope | Member in scope | Auditor in scope | System Admin | Unassigned |
|---|---|---|---|---|---|
| `GET /api/v1/projects` | only explicit PM assignments | only explicit Member assignments | no business project listing | no business data | empty list |
| `POST /api/v1/projects` | allow | deny | deny | deny | n/a |
| `GET /api/v1/projects/{project_id}` | allow | allow | deny | deny | non-disclosing deny |
| `POST /api/v1/projects/{project_id}/archive` | allow in scope | deny | deny | deny | non-disclosing deny |
| `POST /api/v1/projects/{project_id}/members` and `/assignments` | allow in scope | deny | deny | deny | non-disclosing deny |
| `GET /api/v1/projects/{project_id}/members` | allow in scope | allow in scope | deny | deny | non-disclosing deny |
| `POST /api/v1/projects/{project_id}/tasks` | allow in scope | deny | deny | deny | non-disclosing deny |
| `GET /api/v1/projects/{project_id}/tasks` | allow in scope | allow in scope | deny | deny | non-disclosing deny |
| `GET /api/v1/tasks/{task_id}` | allow in scope | allow in scope | deny | deny | non-disclosing deny |
| `PATCH /api/v1/tasks/{task_id}/status` | approved PM transitions in scope | ordinary transition only for own assigned task | deny | deny | non-disclosing deny |
| `GET /api/v1/dashboard/summary` | assigned-project aggregates only | assigned-project aggregates only | no business dashboard | no business data | empty aggregates |
| `GET /api/v1/projects/{project_id}/audit-events` | allow in scope | deny | allow in scope | deny | non-disclosing deny |

The table is a trace of the approved single-role contract. Multi-role cases must follow the owner-selected intersection rule above. Route aliases and relevant scope are included; no new endpoint or business capability is authorized.

## Allowed product files
- `backend/app/projects/routes.py`
- `backend/app/projects/service.py`
- `backend/app/auth/policy.py` (only to implement the owner-selected intersection rule consistently in the reusable authorization helper)
- `backend/tests/test_projects.py`
- `backend/tests/test_tasks_workflow.py`
- `backend/tests/test_dashboard_audit.py`
- `backend/tests/test_auth_policy.py`
- Append-only Worker report: `.team/tasks/CHPMIS-017-worker-report.md`

Any need to change schema/migrations or files outside this list requires a separate scoped review before editing. No frontend, provider, deployment, production, external identity, or real-data work.

## Traceability and acceptance criteria
- Plan Task 5 in `docs/superpowers/plans/2026-10-31-audit-remediation.md`.
- Audit A4-01 and A4-02 in `docs/audit/AUDIT_REMEDIATION.md`.
- Approved role policy in `docs/security/SECURITY_MODEL.md`, `docs/product/USER_ROLES.md`, and `.team/tasks/CHPMIS-003-auth-authorization.md`.
- [ ] HTTP role × endpoint × project-scope behavior matches the matrix above for single-role users.
- [ ] Auditor can read only audit history for explicitly assigned projects; all non-audit business endpoints deny Auditor without disclosing unrelated resource existence.
- [ ] System Admin cannot read or mutate business data, including when a synthetic explicit project membership is seeded.
- [ ] Member reads only assigned projects and can transition only own assigned tasks using the ordinary path; cannot create/assign/archive, mutate another's task, or use PM transitions.
- [ ] Project Manager positive actions remain restricted to assigned project scope; unassigned/cross-project actions fail closed.
- [ ] Department equality alone grants no project/business data access; project lists and dashboard aggregates do not disclose unrelated scopes.
- [ ] Multi-role cases match the owner-selected rule, including System Admin combinations; no implementation assumption is permitted.
- [ ] TDD RED demonstrates the Auditor/business-data gap and any other reproduced matrix defect; GREEN covers all acceptance criteria in scope.
- [ ] Existing lifecycle, task workflow, audit pagination/redaction, and CSRF behavior remain covered by the listed suites.
- [ ] Recorded OpenCode check outputs and exit codes plus the independent Hermes Reviewer's complete source/security assessment are documented; no task closure before the Reviewer approves with no unresolved P1/P2 findings. The OpenCode process deviations remain recorded as NOT_VERIFIED.

## Verification commands
Run from `backend/` only after Worker implementation and with repository virtualenv:
- `.venv\Scripts\python.exe -m pytest -q tests/test_projects.py tests/test_tasks_workflow.py tests/test_dashboard_audit.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_auth_policy.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check app/auth/policy.py app/projects/routes.py app/projects/service.py tests/test_auth_policy.py tests/test_projects.py tests/test_tasks_workflow.py tests/test_dashboard_audit.py` (scoped to the seven CHPMIS-017 allowed files; the 14 other repository-wide findings are tracked separately per owner decision)
- `.venv\Scripts\ruff.exe format --check app/auth/policy.py app/projects/routes.py app/projects/service.py tests/test_auth_policy.py tests/test_projects.py tests/test_tasks_workflow.py tests/test_dashboard_audit.py`
- From repository root: `git diff --check`

Owner decision 2026-11-01: accept the six exact OpenCode check results from run `2026-11-01T12-21-05-verifier-chpmis-017-scoped-independent-authorizat-fe0e` as test evidence and use one independent Hermes Reviewer for the missing source/security assessment, subject to matching the seven tested file hashes before and after review. The verifier runs' denied/unlisted commands and incomplete source verdict remain recorded; they are not reclassified as a clean verifier pass.

## Prompt template
- Owner decision 2026-11-01: preserve the seven-file CHPMIS-017 allowlist, fix only five Ruff I001 findings in four test files, accept Ruff scoped to the seven allowlisted files, and track the 14 out-of-scope repository-wide findings separately. This supersedes the earlier repository-wide lint criterion for CHPMIS-017 only.
- Library: prompts.chat through installed `.agents/skills/prompt-lookup`.
- Template: **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Retrieved full template on 2026-10-30 via prompt-lookup for CHPMIS-015. It requests a senior engineer implementation with bounded feature scope, existing conventions, error handling, tests, documentation, and a clear report.
- Modernized prompt: “Act as the CHPMIS-017 backend authorization Worker. Follow only the approved role/action/scope matrix and the owner's intersection rule: an action is allowed only if every applicable global role and the project-scoped role allow it, with explicit project/task scope still required. Work test-first: add HTTP integration regressions, record RED, implement the smallest fail-closed server-side change, then run only the listed checks. Cover every listed endpoint, assigned and cross-project scope, Auditor audit-only access, System Admin business-data denial, Member assigned-task-only ordinary transitions, department-only denial, and role-combination cases. Preserve existing unrelated dirty work. Modify only the task allowlist; do not change schema, workflow semantics, external identity, or deployment. Report changed files, exact command/output/exit code, role traceability, deviations, and NOT_VERIFIED items. Request independent review; do not self-approve.”

## Human gates and constraints
- Do not broaden the approved role matrix; apply the owner's role-intersection decision exactly and do not infer a union or precedence shortcut.
- Use synthetic fixtures only. No real agency data, external identity provider, production, deployment, push, merge, or cleanup/reset of the working tree.
- The initial checkout is substantially dirty; preserve all existing changes and work serially.
- Report exact checks and exit codes; missing independent evidence is `NOT_VERIFIED`, never PASS.

## Definition of Done
All authorization acceptance criteria have evidence; focused and full backend checks pass; scoped Ruff over the seven allowed files and format checks pass; exact verifier transcript and exit codes are recorded; independent Hermes Reviewer approves with zero unresolved P1/P2 findings; owner-selected policies are reflected in task pack and `OPEN_QUESTIONS.md`; task and ledger are closed with the 14 out-of-scope repository-wide Ruff findings and remaining platform/remote/runtime limitations stated separately.

## Subsequent F1 review observation — 2026-11-01
F1 Reviewer approved the missing-role fix. Its transcript also recognized that `authorize` previously used a supplied `project_id` without comparing the task's parent. The final verdict did not list this helper-only condition. Current HTTP task detail and status callers construct the context from the database task's actual `project_id`, so a reachable HTTP bypass was not established. Owner approved F2; Worker added the comparison and independent Reviewer `t_afd09e45` approved the result.
