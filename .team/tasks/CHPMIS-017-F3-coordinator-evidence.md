# CHPMIS-017-F3 Coordinator Evidence

## Baseline
- Branch `audit-remediation/verify-audit-findings`, starting HEAD `7a27930bd3f80d4d08bcf9ed55ae829c90ca7637`, clean before task-pack additions and Worker dispatch.
- The initial CI reproduction found the five existing Ruff `I001` errors, a format failure in `backend/alembic/versions/0006_bootstrap_trust_boundary.py`, PostgreSQL tests skipped without `TEST_DATABASE_URL`, offline Alembic SQL through revision `0006_bootstrap_trust_boundary`, and Compose config failure when CI synthetic interpolation values were absent. The exact baseline commands/results are recorded in the current conversation; repository-wide backend pytest later passed under reviewed execution.

## Coordinator verification after Worker
All commands ran from repository root against the live Worker diff. These are Coordinator reruns, separate from OpenCode evidence.

| Command | Result | Exit |
|---|---|---:|
| `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py -k empty_global_roles` | 1 passed, 8 deselected, 1 Starlette/httpx deprecation warning | 0 |
| `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_dashboard_audit.py -k empty_global_roles` | 1 passed, 14 deselected, 1 warning | 0 |
| `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py` | 31 passed, 1 warning | 0 |
| `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py` | 13 passed, 1 warning | 0 |
| `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py` | All checks passed | 0 |
| `./backend/.venv/Scripts/ruff.exe format --check backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py` | 6 files already formatted | 0 |
| `git diff --check` | no output | 0 |

Full backend pytest at baseline: `.venv\Scripts\python.exe -m pytest -q` from `backend/` → 138 passed, 2 skipped (PostgreSQL-only), 1 warning, exit 0 under reviewed sandbox execution. PostgreSQL-only command `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` → 2 skipped, exit 0 because `TEST_DATABASE_URL` is unset.

## Independent OpenCode verifier
- First run `2026-11-01T14-18-59-verifier-chpmis-017-f3-independent-verifier-7eaf`, session `ses_e6885a91dffeoJYpcJIbFnQTW5`: timed out at 1200 seconds, exit 1, no outcome, no error events; NOT_VERIFIED. It is not treated as a pass.
- One bounded retry `2026-11-01T14-43-04-verifier-chpmis-017-f3-bounded-opencode-checks-8dcb`, session `ses_e686f9bfdffe4CJjIOxAAHGTvd`, OpenCode Desktop GUI-visible, shared service `http://127.0.0.1:28894`, model not surfaced, cost USD 0, 52,010 input / 7,855 output tokens. Driver exit 0; summary reports two empty-role selectors (2/2), related test suites (31/31), Ruff check, Ruff format and diff check all passed. The exact commands are listed in `.team/tasks/CHPMIS-017-F3-opencode-readonly-checks.md`; the coordinator table above contains exact command results.

## Independent Hermes Reviewer
- Reviewer card `t_fce4ffa1`, separate session `20261101_214030_a58084`, verdict APPROVED with 0 P1/P2/P3. Reviewer read the F3 diff, relevant authorization code and tests. It explicitly retained the first OpenCode timeout as NOT_VERIFIED; the bounded successful retry above completed afterward.

## Dispatch event
- Generic Hermes dispatch selected old parent card `t_4c0b9363` instead of the newly created F3 card. Coordinator immediately stopped/reclaimed that run; the exact F3 Worker was then launched by claim-and-run. `git status`/`git diff` showed no changes from the unintended run. Do not count it as task evidence.

## Verdict
CHPMIS-017-F3 DoD is satisfied for this local synthetic scope. This does not satisfy the overall platform gate: live PostgreSQL upgrades/trigger/concurrency, authenticated browser E2E, remote CI, and the remaining mission findings are still open or NOT_VERIFIED.
