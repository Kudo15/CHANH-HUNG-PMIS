# CHPMIS-017-F2 — Task and Project Context Consistency

## Status and human gate
COMPLETE for local scope: Worker `t_1ef0b522` recorded RED/GREEN and assigned checks; independent Reviewer `t_afd09e45` approved the resulting diff. Parent CHPMIS-017 remains subject to its documented runtime and remote limitations.

## Evidence
In `backend/app/auth/policy.py:172`, the helper resolves the task's parent only when `context.project_id` is absent. When both are present, a direct caller can supply project A and a task from project B. For a user with a global and project role that allows `TASK_READ` in A, the helper checks membership/permissions for A but does not compare the task's actual parent B. This is a code-path observation; a dedicated failing test has not yet been run.

The current HTTP task-detail route (`backend/app/projects/routes.py:320`, `:337`) and transition service (`backend/app/projects/service.py:527`, `:572`) fetch the task and construct the context using its actual database `project_id`. The direct-helper case therefore does not establish a present HTTP exploit. F1 Reviewer transcript noticed the mismatch but its final APPROVED verdict did not include it.

## Approved scoped outcome
Assign a Hermes Worker to verify with a synthetic failing test, then require `authorize` to fail closed when supplied task and project identifiers do not match the resolver's task parent, or the parent cannot be resolved. Preserve valid matching cases, task-only resolution, global project creation, role intersection, HTTP behavior and unrelated dirty work. Use TDD and independently review the resulting diff. No schema, external provider, workflow or new business privilege.

Allowed changes: `backend/app/auth/policy.py`, `backend/tests/test_auth_policy.py`, and `.team/tasks/CHPMIS-017-F2-worker-report.md`. Preserve existing dirty work. Do not stage, commit, deploy, edit other files, change schema or use external services. Coordinator maintains ledger.

Real Worker prompt source: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template, retrieved through the installed prompt-lookup skill and recorded in the parent pack.

Modernized task prompt: act as the bounded CHPMIS authorization Worker; inspect the approved matrix, shared helper and actual callers before editing; demonstrate the mismatched task/project case with a failing synthetic regression, implement the smallest fail-closed correction, preserve legitimate matching and task-only contexts plus existing dirty work, run the exact listed checks, record outputs, exit codes and deviations, and request independent review.

Required checks, from repository root; include at least one new test whose name contains `task_project_mismatch`:
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py -k task_project_mismatch` — RED then GREEN.
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests`
- `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/auth/policy.py backend/tests/test_auth_policy.py`
- `./backend/.venv/Scripts/ruff.exe format --check backend/app/auth/policy.py backend/tests/test_auth_policy.py`
- `git diff --check`

## Definition of Done
Record RED and GREEN with exact commands, outputs and exit codes, changed files, requirement trace, real prompt template, all assigned checks, warnings and limits in the Worker report. Confirm matching IDs and task-only resolution remain allowed where policy permits; mismatched or unresolvable parent fails closed. Do not claim repository-wide Ruff passes. Fresh independent review is required. Previously documented OpenCode process deviations, 14 unrelated Ruff findings, and remote/runtime limits remain.
