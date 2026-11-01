# Task Pack — CHPMIS-017-F1 Missing Project Role

## Task, role, authority
- Task ID: CHPMIS-017-F1. Role: Hermes Worker. Parent: CHPMIS-017 endpoint authorization matrix.
- Status: COMPLETE — Worker `t_611c0336` recorded RED/GREEN and seven GREEN checks; independent Reviewer `t_a17ac87e` approved F1. A separate helper-context inconsistency is recorded in the parent task.
- Objective: investigate and, if reproduced, correct a fail-closed gap in the approved shared authorization helper. This implements the already-approved intersection contract; do not add any new business policy or capability.
- Preserve the existing dirty checkout. Only `backend/app/auth/policy.py`, `backend/tests/test_auth_policy.py`, and a new Worker report `.team/tasks/CHPMIS-017-F1-worker-report.md` may be modified. No schema, migration, config, other files, staging, commits, deployment, or external services. Coordinator maintains ledger.

## Evidence and hypothesis
At `backend/app/auth/policy.py:193`, project-role enforcement only occurs when `project_role is not None`. If a resolver reports explicit project assignment but returns no project role (or lacks a concrete implementation), all global permissions can pass and the function can return true without a project-role intersection. `MockProjectScopeResolver` in `backend/tests/test_auth_policy.py` lacks a concrete `get_user_project_role` implementation. The actual database model has a non-null role column; do not claim a current HTTP exploit without evidence. The approved contract in the parent pack requires the project membership role to permit each scoped action.

## Required behavior and RED/GREEN
- First inspect the helper, resolver implementations, existing policy tests, callers, approved intersection and scope. Demonstrate the missing-role case with a focused meaningful regression against real `authorize`; record the failing assertion before implementation. Cover assignment true with missing role and invalid role as fail-closed; cover valid roles with positive and negative intersections. Ensure unresolved task parent cannot grant task access. Do not alter global project creation semantics.
- Implement the smallest correction if the hypothesis is confirmed; require an actual permitted project role for scoped authorization. Preserve unrelated dirty work and meaningful existing assertions. If test resolver fixtures previously omitted role data, supply explicit valid role data consistent with each test's intended scenario; do not weaken expected behavior.
- If the diagnosis or allowed scope is inadequate, report BLOCKED instead of guessing or expanding scope.

## Verification commands from repository root
The following focused selector is explicitly added to capture the RED and GREEN; name at least one new test with `missing_project_role`:
1. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k missing_project_role` — run before and after implementation, record exact output and exit code.
2. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
3. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
4. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests`
5. `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/auth/policy.py backend/tests/test_auth_policy.py`
6. `./backend/.venv/Scripts/ruff.exe format --check backend/app/auth/policy.py backend/tests/test_auth_policy.py`
7. `git diff --check`

Report all output and exit codes, failures and warnings. Do not claim repository-wide Ruff passes; its 14 out-of-scope findings remain tracked. A fresh independent review is required after changes; the prior Hermes approval concerns the earlier hash.

## Prompt template trace
Real prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template, retrieved through the installed prompt-lookup skill and recorded in the parent pack.

Modernized: act as the bounded CHPMIS authorization Worker; inspect before editing, reproduce the missing-role fail-open condition with a failing test, implement the smallest deny-by-default correction consistent with the approved global/project-role intersection, preserve valid behavior and dirty work, run only assigned verification, record exact evidence and request independent review. Do not broaden role permissions.

## Definition of Done
The report records Task ID, role, scope, real template, requirement trace, RED and GREEN with exact commands/output/exit codes, modified files, full assigned verification, limits and follow-up review. All GREEN checks exit 0; no policy expansion or unrelated edits; Coordinator updates ledger and obtains independent review.

## Dispatch blocker — 2026-11-01
Automatic approval review rejected exact-card Worker launch because it may modify shared authorization policy behavior, which is human-gated, and the owner had not explicitly approved this newly proposed F1 implementation. No Worker ran and no product file changed from that attempt. Owner subsequently explicitly approved the F1 task pack and its specified change.
