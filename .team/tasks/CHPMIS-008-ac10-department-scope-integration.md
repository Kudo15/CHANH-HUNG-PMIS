# Task Pack — CHPMIS-008 AC-10 Department Scope Integration Test

## Task identity and roles
- Task ID: CHPMIS-008.
- Roles: Hermes Worker, independent OpenCode Tester/Verifier, independent Hermes Reviewer.
- Status: COMPLETE — Worker checks pass, OpenCode independently reran both pytest commands, and Hermes Reviewer approved static review. AC-10 evidence gap is closed for the scoped department-matched nonmember case.
- Trace: AC-10 in `ACCEPTANCE.md`; approved explicit-membership policy in `OPEN_QUESTIONS.md` HG2 and `backend/app/auth/policy.py:126`.
- Design/plan: `docs/superpowers/specs/2026-10-30-chpmis-008-ac10-department-scope-integration-design.md`; `docs/superpowers/plans/2026-10-30-chpmis-008-ac10-department-scope-integration.md`.

## Objective
Add a backend API integration regression test proving that matching `User.department` to `Project.lead_department_id` does not grant access in the absence of an explicit `ProjectMember` row. This closes the specific AC-10 evidence gap identified after CHPMIS-006.

## Authority and scope
- This task tests the already-approved HG2 policy. It does not introduce or alter business/security policy.
- Only allowed product/test file: `backend/tests/test_projects.py`.
- Do not modify production code, auth policy, routes, schema, migrations, acceptance statuses, dependencies, or other tests unless the coordinator approves a task-pack change.
- No real agency data, external services, production access, deployment, merge, push, staging, or commit.
- Preserve the dirty/untracked baseline. Run serially in `dir:D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`; no Hermes worktree assumption is authorized.

## Required scenario and assertions
Use the existing SQLite-backed FastAPI test helpers in `backend/tests/test_projects.py` and synthetic IDs. Create an in-scope Project Manager, a Member with `department` equal to a project's `lead_department_id`, and a task under that project. Leave the department-matched Member without any `ProjectMember` row.

Through the department-matched Member's authenticated session, assert:
- `GET /api/v1/projects` returns no project IDs; `GET /api/v1/dashboard/summary` has no projects and zero project/task totals.
- `GET /api/v1/projects/{project_id}`, `/members`, `/tasks`, `/api/v1/tasks/{task_id}`, and `/api/v1/projects/{project_id}/audit-events` return 404.
- With valid CSRF, `PATCH /api/v1/tasks/{task_id}/status` and `POST /api/v1/projects/{project_id}/archive` return 404.
- Task remains `open`; project remains `active`; no `task:transition` or `project:archive` audit event is written for the denied request.
- Fixture explicitly confirms the department values match and the caller has no membership row.

Do not test or alter policy through mocks; these are real local API/database integration checks. Do not add unrelated cross-project cases already covered by existing tests.

## Prompt templates
- Worker: prompts.chat **Feature coding template**, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved and modernized for this test-only task. Source is recorded in CHPMIS-007 task pack and `.team/ledger.md`.
- Tester: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, retrieved and adapted for read-only independent verification; do not follow its generic TODO-file instruction, which is outside this task's allowlist.
- Reviewer: prompts.chat **Senior Code Reviewer (severity-ranked)**, ID `cmv9n79m30005ku060pzornri`, retrieved and adapted for read-only scope/security review.

## Verification commands
Run from `backend/` only:
- Focused: `.venv\Scripts\python.exe -m pytest -q tests/test_projects.py::test_department_match_without_explicit_project_membership_is_denied_ac10`
- Full suite: `.venv\Scripts\python.exe -m pytest -q`
- Lint: `.venv\Scripts\ruff.exe check .`

These commands exist in the repository's prior verification records. Record exact output and exit code; if the venv executable is absent, stop and report `NOT_VERIFIED` instead of installing packages.

## Definition of Done
- Worker adds only the named test, demonstrates matching department and absent explicit membership, runs TDD-style verification without temporary product mutation, and reports exact checks.
- OpenCode Tester makes no edits, independently runs the focused test and full backend suite, and records commands/results/exit codes.
- Hermes Reviewer is a separate read-only role run after Tester and returns `APPROVED` or `CHANGES_REQUESTED` with any finding at `file:line` and priority.
- Coordinator records all run traces in `.team/ledger.md`; update AC-10 only when independent evidence and review justify it.

## Known workspace limitation
`backend/` was already untracked before CHPMIS-008. Git status cannot isolate individual test-file changes through a regular tracked diff. Worker must report the exact modified file; Tester and Reviewer should inspect the named function and workspace scope. Do not stage or commit as a workaround.

## Worker handoff — Hermes
- Card `t_46c85ad5`, run #27, profile `default`, session `20261030_171607_0a207b`, workspace `dir:D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`, status `done`; no model/provider override, exact model/provider not exposed.
- Reported changed file: `backend/tests/test_projects.py`; implementation is `test_department_match_without_explicit_project_membership_is_denied_ac10` at line 430.
- Worker verification metadata: focused pytest 1 passed, exit 0 (1 warning); full backend pytest 62 passed / 1 skipped, exit 0 (1 warning); Ruff check all passed, exit 0.
- Coordinator read the test body: fixture sets matching synthetic department values and asserts no membership row; it covers scoped list/dashboard, non-disclosing reads, valid-CSRF denied writes, unchanged state and absent denied-write audit events. Independent verification/review remains pending.

## Independent Tester handoff — OpenCode
- Run `2026-10-30T10-23-36-verifier-chpmis-008-t1-independent-backend-verifi-3505`; session `ses_e73a9e09dffeh1NaKxghstDr0T`; `gui_visible=true`; `role=verifier`; model ID not exposed; cost 0 recorded; tokens 16800/2321/1045.
- Outcome `blocked` / `ROLE_RESULT: blocked`. Both allowed pytest commands were denied before execution with exact output `{"error":{"type":"permission.rejected","message":"Permission denied: shell"}}`; run record exit 0 (role correctly reported blocked), helper process exit 1. No test count or pytest exit code exists.
- Static source inspection by the initial Tester found the expected AC-10 assertions and two minor review notes: 404 body itself is not asserted, and denied-audit queries filter by action without target/actor. No files were modified during that run.

### Authorized retry — OpenCode independent pytest execution (2026-10-31)
- User explicitly authorized enabling shell for this verifier and rerunning only the two pytest commands. `role-verifier` continues to have `edit: deny`; its shell allowlist contains the two exact `.venv\\Scripts\\python.exe -m pytest -q ...` commands.
- Run `2026-10-30T23-02-55-verifier-chpmis-008-t1-independent-backend-verifi-f8f9`; session `ses_e70f2ada4ffeY96OSNGghKnAKQ`; `gui_visible=true`; OpenCode CLI `v2.2.2`; no model override, `model_used=null`; cost recorded `0`; tokens input/output/reasoning `12068/1624/597`.
- Focused command from `backend/`: `.venv\\Scripts\\python.exe -m pytest -q tests/test_projects.py::test_department_match_without_explicit_project_membership_is_denied_ac10` — `1 passed, 1 warning in 2.87s`, exit 0.
- Full backend command: `.venv\\Scripts\\python.exe -m pytest -q` — `62 passed, 1 skipped, 1 warning in 6.22s`, exit 0. The warning is the existing Starlette/httpx TestClient deprecation.
- Tester confirmed the fixture precondition, scoped list/dashboard, five 404 reads, two valid-CSRF denied writes, unchanged state, and absent denied-write audit events by executing the test. Ruff was outside this Tester’s two-command scope; Worker’s Ruff result remains reported separately.

## Independent Reviewer handoff — Hermes
- Card `t_e1d1d599`, run #28, profile `default`, reviewer session `20261030_172626_500a95`, workspace `dir:D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`, status `done`; model/provider/cost not exposed.
- Verdict: `APPROVED`, zero P1/P2/P3 findings. Reviewer statically verified the synthetic department match, absent membership, list/dashboard scoping, five 404 read paths, two valid-CSRF denied writes, unchanged task/project state, and no denied-write audit events.
- Two P4 informational notes: 404 response bodies are not asserted (matches suite style); audit queries filter globally by action, which reviewer considered stricter in the isolated SQLite test database. Neither was blocking.
- Review evidence was completed before the authorized OpenCode retry; the retry subsequently provided independent execution evidence for both required pytest commands.
