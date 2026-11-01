# Task Pack — CHPMIS-017-T2 Ruff import-order cleanup

## Task ID, role, status
- Task ID: CHPMIS-017-T2
- Role: Hermes Worker, implementation-only
- Status: IMPLEMENTATION COMPLETE — Hermes Worker card `t_d96d42de`; five scoped checks passed. Independent verification remains separate.
- Parent: CHPMIS-017 endpoint authorization matrix.
- Worker follow-up is limited to import ordering in four existing test files. Do not alter product behavior.

## Objective
Resolve the five Ruff `I001` findings reported by OpenCode run `2026-11-01T05-39-48-verifier-chpmis-017-corrected-independent-verific-ad39` in only the four CHPMIS-017 test files below. Preserve all existing behavior and unrelated dirty work. Do not change the task scope or fix any of the 14 separately tracked repository-wide findings.

## Allowed files
- `backend/tests/test_auth_policy.py` — Ruff findings at prior lines 1 and 311.
- `backend/tests/test_dashboard_audit.py` — Ruff finding at prior line 1.
- `backend/tests/test_projects.py` — Ruff finding at prior line 1.
- `backend/tests/test_tasks_workflow.py` — Ruff finding at prior line 1.

No production files, migrations, other tests, task packs other than this append-only report, or configuration files may be changed. Do not run broad `ruff --fix` against a directory; if using Ruff's fix, pass only the four explicit allowlisted files and inspect the resulting diff.

## Required implementation behavior
- Change import organization only to satisfy Ruff `I001` in the four files.
- Do not change authorization logic, assertions, fixtures, test names, or runtime behavior.
- Do not create behavioral tests for this formatting-only correction. Existing focused suites below must still pass.

## Verification commands
Run from repository root and report exact output and exit code for each:
1. `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/tests/test_auth_policy.py backend/tests/test_dashboard_audit.py backend/tests/test_projects.py backend/tests/test_tasks_workflow.py`
2. `./backend/.venv/Scripts/ruff.exe format --check backend/tests/test_auth_policy.py backend/tests/test_dashboard_audit.py backend/tests/test_projects.py backend/tests/test_tasks_workflow.py`
3. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
4. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
5. `git diff --check`

Repository-wide Ruff produced 14 findings outside this task's allowlist. The owner explicitly chose scoped Ruff for the seven CHPMIS-017 files and separate tracking for those 14 findings. Do not claim repository-wide Ruff passes.

## Prompt template trace
- Real library template: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Retrieved on 2026-10-30 through installed prompt-lookup and recorded in the parent task pack.
- Modernized for this bounded Worker task: “Act as the CHPMIS-017 test-maintenance Worker. Modify only the four allowlisted test modules and only reorder imports required by Ruff I001. Preserve all test logic and existing dirty work. Do not change application code, other tests, migrations, Ruff configuration, or task acceptance. Run only the listed scoped Ruff, focused pytest, and whitespace checks. Report exact files, diff, outputs, exit codes, and deviations; do not claim repository-wide Ruff passes because 14 findings outside this scope are tracked separately.”

## Definition of Done
- The Worker diff changes only import ordering in the four allowed tests and the append-only Worker report.
- All five listed commands exit 0.
- No behavior changes, unrelated formatting, or scope expansion.
- Report is appended to `.team/tasks/CHPMIS-017-worker-report.md`; independent verifier and Hermes Reviewer remain separate follow-on roles.
