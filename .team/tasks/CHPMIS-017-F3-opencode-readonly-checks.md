# CHPMIS-017-F3 — OpenCode Read-Only Check Set

## Role and status
- Role: OpenCode verifier, read-only
- Task: CHPMIS-017-F3 empty-global-role regression
- Context: Hermes Worker `t_e4f5224f` submitted; independent Hermes review `t_fce4ffa1` approved with 0 findings. The prior OpenCode run `2026-11-01T14-18-59-verifier-chpmis-017-f3-independent-verifier-7eaf` timed out after 1200 seconds without a result, so this is a bounded retry with a short command set. The timeout remains in history.

## Instructions
Do not edit files. Do not perform source review, exploratory search, or rerun unrelated tests. Run the following six commands from the repository root, one shell call per command, and stop after them. Report exact output and exit code for each. If a command is rejected by role permissions, record it as blocked; do not probe alternatives or change policy.

1. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py -k empty_global_roles`
2. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_dashboard_audit.py -k empty_global_roles`
3. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
4. `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py`
5. `./backend/.venv/Scripts/ruff.exe format --check backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py`
6. `git diff --check`

End with a concise evidence list and `ROLE_RESULT: done|blocked`.
