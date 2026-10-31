# CHPMIS-007 — Project Workbench

## Task identity and role

- **Task ID:** CHPMIS-007
- **Role:** Worker (Hermes CLI Kanban; explicit dispatch)
- **Prompt template:** `Feature coding template`, prompts.chat ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved via installed `.agents/skills/prompt-lookup/` and modernized for this task. Source: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- **Harness routing:** Worker uses the active Hermes `default` profile without model/provider/effort override. Codex remains coordinator; Codex default is reserved for Tester.
- **Workspace:** Existing repository directory, `dir:D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`. Run serially; do not create a worktree because the accepted baseline includes untracked files.
- **Design/plan:** `docs/superpowers/specs/2026-10-30-project-workbench-design.md`; `docs/superpowers/plans/2026-10-30-chpmis-007-project-workbench.md`.

## Objective

Deliver a responsive frontend Project Workbench that lets an authenticated user navigate projects they are authorized to access, understand the selected project, and use already-approved project/task actions through existing API contracts.

## Scope and file allowlist

Product-code changes are limited to:

- `frontend/src/App.tsx`
- `frontend/src/components/ProjectTaskManager.tsx` or a new focused `frontend/src/components/ProjectWorkbench.tsx`
- `frontend/src/App.test.tsx` or focused test files under `frontend/src/**`
- styles under `frontend/src/**` only when needed by the feature

No backend, migrations, API schema, auth policy, role matrix, workflow semantics, package dependencies, deployment, or environment changes. Preserve all pre-existing dirty/untracked files; do not clean/reset/stage/commit.

## Approved behavior and constraints

- Session comes from `/api/v1/auth/session`; keep `csrf_token` in React memory only. Use cookie credentials for protected reads. Send `X-CSRF-Token` on mutations. No fake login and no authorization decisions trusted solely to the UI.
- Project list is the user's authorized project list. Load members, tasks, dashboard and audit only for a selected returned project; do not guess IDs or fetch cross-project aggregates.
- Derive the selected-project role by matching session `user.id` to that project's member list. Global Project Manager role only enables create-project affordance. Server is authoritative for every access and mutation.
- The service adds a project creator as an initial project member with role `project_manager`. Task assignee choices must be existing members of the selected project. Display opaque member IDs/roles; no staff directory/add-member control exists in scope.
- In-scope Project Manager may create tasks, assign to existing project members, and archive an active project. Archive requires confirmation and makes project UI read-only.
- Member may transition only their assigned task via approved ordinary path. Auditor is read-only. Project Manager may cancel unfinished tasks and reopen done tasks to in_progress. Exact matrix: `open -> in_progress`; `in_progress -> blocked|done`; `blocked -> in_progress`; PM may additionally cancel unfinished and reopen `done -> in_progress`; `cancelled` terminal.
- Use only existing endpoints and payloads, confirming route/schema names in backend source before wiring. No business policy assumptions beyond those above.
- Use synthetic frontend test data. No real IdP, production service, Docker/PostgreSQL runtime, or external provider.

## Acceptance criteria

1. Authenticated user sees a responsive workbench with their authorized project list, project search, selected-project metadata, member IDs/roles, scoped dashboard summary, project task list, and project audit history.
2. Loading, empty, unauthenticated, and request-error states are clear and do not leak protected project details.
3. Project search and task search/status filtering operate locally over already-authorized loaded results.
4. A global Project Manager can create a project using existing API fields; creation is reflected after refresh.
5. A selected-project Project Manager can create a task and choose assignee only from that project's member response.
6. Task action affordances follow project role, task assignee, task status, and the approved exact transition matrix; UI keeps server enforcement authoritative.
7. Selected-project Project Manager can confirm archiving an active project; archived project has no create/task/status/archive controls and remains readable.
8. Mutations send cookie credentials plus in-memory `X-CSRF-Token`, handle errors without leaking protected data, and refresh relevant view state after success.
9. Focused tests show meaningful RED before implementation and GREEN afterward. Repository-defined frontend test, lint, and build checks run with exact outcomes; E2E is run if runnable without external services or marked NOT_VERIFIED.
10. No files outside the allowlist are modified by the Worker; no new endpoint, schema, role, workflow, or dependency is added.

## Definition of Done

- Acceptance criteria are implemented and mapped to tests/evidence.
- Exact commands, results, and exit codes are reported; unknown or unavailable evidence is `NOT_VERIFIED`.
- Existing dirty baseline remains untouched outside the task allowlist.
- Implementation handoff contains changed-file list, RED/GREEN evidence, remaining risks/gaps, and no claim of independent approval.

## Required execution method

Follow the plan task by task. Use TDD: tests first, observe RED, then implement. Inspect the existing UI, frontend tests, route handlers and Pydantic schemas before coding. Keep changes narrow and accessible. Do not alter acceptance statuses or ledger; the coordinator records the observed run after handoff. Stop and report a concrete blocker if a required behavior cannot be supported by existing contracts without changing backend policy/scope.

### Modernized Worker prompt

Implement CHPMIS-007 using the retrieved Feature coding template and only this task pack/spec/plan. First inspect the charter, ledger, current task pack, relevant acceptance and approved policy docs, exact existing route/schema contracts, and preserve the already-dirty checkout. Work only in the allowlist and use TDD: add focused behavior tests, capture a meaningful RED result, implement the smallest frontend-only change, then capture GREEN evidence. Build a responsive authorized project workspace using only existing endpoints. Keep session CSRF in memory, send cookie credentials and CSRF headers on mutation, derive project role by matching current user ID to selected-project members, limit assignees to returned members, implement only the approved transitions and archive behavior, and display only the selected dashboard item. Never create backend/API/schema/policy/role/workflow changes, new dependencies, auth shortcuts, arbitrary membership/assignee entry, or unrelated cleanup. Run only repository-defined frontend checks listed here, record exact commands/results/exit codes, and mark unavailable runtime checks NOT_VERIFIED. Do not edit ledger/acceptance evidence or claim independent review. Return changed files, acceptance/test mapping, RED/GREEN evidence, results, and gaps.

