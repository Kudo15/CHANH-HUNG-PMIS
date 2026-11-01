# Task Pack — CHPMIS-017 OpenCode Independent Verifier

## Task ID, role, status
- Task ID: CHPMIS-017-T1
- Role: OpenCode `role-verifier`, independent and read-only
- Status: NOT_VERIFIED — the approved 2026-11-01 run passed all six checks, but its combined diff was truncated and an unlisted shell command was denied. A source-review follow-up is needed.
- Target checkout: existing project workspace, preserving its full current state.
- Worker card: Hermes `t_4c0b9363`, run #80, session `20261101_115822_638b86`, status `review`.

## Objective
Independently verify the Worker implementation for CHPMIS-017 against the owner-approved role-intersection policy, every route in the endpoint matrix, and the task acceptance criteria. Do not edit files, fix findings, run migrations, start services, or perform database/runtime actions. Read the task pack, Worker report, changed diff, and actual test output before concluding.

## Commands allowed for this run
For any approved follow-up, run only these exact checks, one at a time, from repository root. The paths name the backend virtualenv explicitly so shell working-directory defaults cannot redirect execution. Git whitespace check also runs from repository root.

1. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
2. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
3. `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests`
4. `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/auth/policy.py backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_auth_policy.py backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
5. `./backend/.venv/Scripts/ruff.exe format --check backend/app/auth/policy.py backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_auth_policy.py backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
6. `git diff --check`

The independent source review also needs only these read-only inputs, using the already-allowed `cat *` and `git *` permissions:
- `cat .team/tasks/CHPMIS-017-endpoint-authorization-matrix.md`
- `cat .team/tasks/CHPMIS-017-worker-report.md`
- `git diff -- backend/app/auth/policy.py backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_auth_policy.py backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`

The root-relative paths are the corrected retry form. Owner decision 2026-11-01 supersedes the repository-wide Ruff command above with Ruff scoped to the seven allowed CHPMIS-017 files; the 14 findings outside those files remain separately tracked. A further verifier run still requires fresh approval; retain `shell * deny` and `edit * deny`.

All outputs and exit codes must be reported exactly. Any command denial, skip, failure, unexplained change, or evidence gap is `NOT_VERIFIED` or a finding, not PASS. Do not add diagnostic shell commands.

## Review criteria
- The effective action must be allowed by every global role, then by the user's explicit project membership role; task assignment and ordinary-vs-PM transition rules remain additional constraints.
- System Admin has no project/task/dashboard/audit business-data access, including with synthetic project membership.
- Auditor reads only audit history for explicitly assigned projects.
- Member has only assigned-project reads and own-assigned-task ordinary state changes.
- Project Manager actions require explicit project assignment; no cross-project access.
- Department-only match grants no access.
- Global and project membership role combinations follow the owner's intersection decision, including PM+Auditor audit-read overlap and denial for combinations without a common permission.
- Confirm route alias `/assignments`, task parent-project resolution, and read non-disclosure.
- No schema, migration, unrelated source, or documentation mutation is in the Worker diff.

## Boundaries
- Do not use or expose secrets, external services, production, real agency data, or live database/runtime resources.
- Do not edit, stage, commit, deploy, push, merge, or change permission rules beyond the six commands above.
- Global OpenCode `shell * deny` and `edit * deny` rules remain. Any command-specific permission needed is limited to the exact six commands in this pack.
- Model/provider are inherited from OpenCode's configured default and must be reported only if surfaced. The run is billed; dispatch only after explicit owner approval.

## Evidence report format
Record the OpenCode run ID, session ID, CLI/service/GUI status, model/cost/tokens if visible, exact command/output/exit code, observed file changes, acceptance trace, findings with file/line and severity, and NOT_VERIFIED limits. Finish with exactly `SUMMARY: ...` and `ROLE_RESULT: done|blocked`.

## Definition of Done
All six checks complete with exit 0, independent source review finds no P1/P2 authorization gap or scope violation, and the Coordinator records the read-only verifier's evidence in this file and `.team/ledger.md`. If any criterion fails or evidence cannot be obtained, record it and leave CHPMIS-017 open.

## First approved run evidence — blocked
- Run: `2026-11-01T05-35-16-verifier-chpmis-017-independent-endpoint-authoriz-3085`; session `ses_e6a652279ffewU4TOlNMyI7zBt`; OpenCode v2.2.2; service `http://127.0.0.1:28894`; GUI listed; default model not surfaced; cost USD 0; 97,017 input / 5,554 output tokens; duration 112,040 ms; driver exit 1; `ROLE_RESULT: blocked`.
- Root cause: commands 1–5 were invoked with the repository root as the shell cwd even though the approved venv and pytest configuration live in `backend/`. PowerShell returned `The module '.venv' could not be loaded` (exit 1) for each Python/Ruff command. No check result is verified by those attempts.
- Command 6, `git diff --check`, returned no output, exit 0.
- The verifier also ran unlisted diagnostics `git status`, `ls .venv\Scripts\python.exe`, `ls -la`, and `ls .venv`; these did not modify files. `git status` observed the existing dirty workspace. This is a verifier process deviation and the run remains blocked.
- No source change was made by the verifier. Acceptance/source-review criteria remain NOT_VERIFIED. A retry and the separate Hermes Reviewer have not been dispatched; each billed run requires owner approval.
- Exact failed output for each attempted check: `.venv\Scripts\python.exe` / `.venv\Scripts\ruff.exe : The module '.venv' could not be loaded. For more information, run 'Import-Module .venv'.`; PowerShell `CommandNotFoundException`, `CouldNotAutoLoadModule`, exit 1.
- Driver summary: `Executed six verification commands: 1) pytest on three test files failed (module .venv not found); 2) pytest on auth policy failed (same); 3) pytest on all tests failed (same); 4) ruff check failed (same); 5) ruff format check failed (same); 6) git diff --check passed with no output. Five commands failed due to missing virtual environment, one passed.`

## Corrected retry evidence — blocked
- Run: `2026-11-01T05-39-48-verifier-chpmis-017-corrected-independent-verific-ad39`; session `ses_e6a60fceeffeekg6ngy2rsimzP`; OpenCode v2.2.2; service `http://127.0.0.1:28894`; GUI listed; model not surfaced; cost USD 0; 116,375 input / 1,452 output tokens; duration 89,881 ms; driver exit 1 (`ROLE_RESULT: blocked`; CLI exit 0).
- Exact results: (1) focused project/task/dashboard pytest — `28 passed, 1 warning in 4.56s`, exit 0; (2) auth-policy pytest — `11 passed, 1 warning in 1.21s`, exit 0; (3) full backend pytest — `136 passed, 2 skipped, 1 warning in 7.87s`, exit 0; (4) Ruff — `Found 19 errors. [*] 19 fixable with --fix.`, exit 1; (5) format check — `7 files already formatted`, exit 0; (6) `git diff --check` — no output, exit 0.
- Ruff findings: five I001 findings are in the CHPMIS-017 allowlist: `backend/tests/test_auth_policy.py` (lines 1 and 311), `backend/tests/test_dashboard_audit.py` (line 1), `backend/tests/test_projects.py` (line 1), and `backend/tests/test_tasks_workflow.py` (line 1). Fourteen more I001 findings are outside this task's file allowlist: five Alembic revisions (`0002`–`0006`) and nine test modules (`test_admin_bootstrap.py`, `test_audit_atomicity.py`, `test_auth_oidc.py`, two locations in `test_auth_remediation.py`, `test_auth_session.py`, `test_health.py`, `test_oidc_client.py`, `test_postgresql.py`). No files were edited by the verifier.
- Retry command log contained exactly the six listed checks and no extra diagnostics. The verifier task pack was supplied in the run prompt, but the transcript does not show reads of the endpoint matrix, Worker report, or scoped diff; independent source/acceptance review is therefore NOT_VERIFIED. The OpenCode run is blocked; the conditional Hermes Reviewer approval is not triggered. Do not expand this task's product-file allowlist or alter its DoD without the owner's decision.
- The task acceptance requires repository-wide Ruff, which fails on 14 out-of-scope files as well as five in-scope test import blocks. Further implementation scope and any additional billed Worker/OpenCode/Reviewer runs require a fresh owner decision. Full Ruff output is preserved in the run's `stdout.log` under the OpenCode role-run directory.

## Owner scope decision — 2026-11-01
- Owner selected: keep the existing CHPMIS-017 file allowlist; correct only the five in-scope Ruff import-order findings; accept Ruff scoped to the seven allowed files; track the 14 out-of-scope findings separately.
- The repository-wide Ruff result above remains recorded as a failure. It is not being represented as a pass; the task-specific verification criterion is revised by the owner decision. Source-review and independent Reviewer evidence are still outstanding.

## Worker follow-up — 2026-11-01
- Hermes Worker card `t_d96d42de` completed the five I001 fixes in the four allowlisted test modules. Its report records all five assigned checks at exit 0: scoped Ruff, scoped format, focused pytest (28 passed), auth-policy pytest (11 passed), and `git diff --check`.
- Coordinator inspection confirms the observed CHPMIS-017 edits in those modules are import ordering; pre-existing authorization/test changes remain part of the already-dirty implementation baseline. No out-of-scope source edit was observed.
- Worker transcript shows additional read-only `git diff` and `git status --short` diagnostics outside the enumerated verification commands, then repeated scoped checks. The task pack explicitly allowed file-scoped Ruff `--fix`; the run used it only on the four allowlisted modules. This command-list deviation is recorded; no consequential scope expansion was observed.
- Independent source review and six-check verifier follow-up remain pending fresh owner approval for another billed OpenCode run. The earlier conditional Hermes Reviewer authorization was not triggered by the blocked verifier result.

## Scoped verifier run — 2026-11-01
- Run `2026-11-01T12-21-05-verifier-chpmis-017-scoped-independent-authorizat-fe0e`, session `ses_e68f1963cffe7p61NrecVAEWYX`; OpenCode v2.2.2, service `http://127.0.0.1:28894`, GUI listed, model not surfaced, cost USD 0, 212672 input / 2892 output tokens, duration 187598 ms. Driver exit 0 and agent `ROLE_RESULT: done`; stderr empty.
- The six commands above each returned exit 0: (1) `28 passed, 1 warning in 5.07s`; (2) `11 passed, 1 warning in 1.26s`; (3) `136 passed, 2 skipped, 1 warning in 8.19s`; (4) `All checks passed!`; (5) `7 files already formatted`; (6) no output. Warnings concern Starlette's deprecated httpx test client integration.
- The endpoint matrix and Worker report were read without truncation. The combined seven-file `git diff` returned exit 0 but tool metadata records `truncated: true`, showing only lines 683–1951; the first 682 lines were not shown to the verifier. Source review of the complete diff is therefore NOT_VERIFIED despite its self-reported conclusion.
- Process deviations: the agent also ran unlisted read-only `git status` and attempted an unlisted `echo` for its summary; the latter was rejected with `Permission denied: shell` and did not execute. The task pack treats command denial and evidence gaps as NOT_VERIFIED. No rule was broadened after the denial.
- Coordinator added one exact allow rule for the owner-approved scoped Ruff command before dispatch, retaining `shell * deny` and `edit * deny`; the first guarded config edit attempt exited 1 without writing due to a newline mismatch, and the corrected LF-aware edit succeeded. The three other Python rules and scoped format rule were already present. No product source was edited by Coordinator.
- The verified check outputs remain evidence; completion requires an independent read of the missing diff portions and a separate Hermes Reviewer. The follow-up proposal is `.team/tasks/CHPMIS-017-verifier-source-followup.md`.
