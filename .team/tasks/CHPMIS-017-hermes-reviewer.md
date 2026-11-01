# Task Pack — CHPMIS-017 Independent Hermes Reviewer

## Task, role and objective
- Task ID: CHPMIS-017-R1; role: independent Hermes Reviewer, separate session from Worker `t_4c0b9363` and cleanup Worker `t_d96d42de`.
- Owner authorized one review on 2026-11-01, with recorded OpenCode checks retained as test evidence and the missing full source/security assessment assigned here.
- Review the current dirty checkout; preserve all existing changes. Judge the implementation, do not edit source, tests, configuration, task files, reports, ledger, or environment. No commit, push, deploy, migrations, production, external identity, or live services.

## Inputs and evidence
Read `.team/CHARTER.md`, `.team/tasks/CHPMIS-017-endpoint-authorization-matrix.md`, `.team/tasks/CHPMIS-017-worker-report.md`, `.team/tasks/CHPMIS-017-opencode-verifier.md`, `.team/tasks/CHPMIS-017-verifier-source-followup.md`, and `.team/tasks/CHPMIS-017-review-route-proposal.md`. Review each of the seven diffs individually and inspect relevant surrounding code, tests and call paths as needed:
- `git diff -- backend/app/auth/policy.py`
- `git diff -- backend/app/projects/routes.py`
- `git diff -- backend/app/projects/service.py`
- `git diff -- backend/tests/test_auth_policy.py`
- `git diff -- backend/tests/test_projects.py`
- `git diff -- backend/tests/test_tasks_workflow.py`
- `git diff -- backend/tests/test_dashboard_audit.py`

Inputs are not a substitute for your own analysis. If a read or diff is truncated, inspect in smaller sections and state any unresolved evidence gap. The pre-existing checkout contains unrelated dirty files; do not attribute all git changes to CHPMIS-017. Coordinator independently checks seven file hashes before and after review.

## Required assessment
Trace every endpoint in the matrix to actual enforcement and meaningful tests. Assess all global-role intersection cases, project membership role and explicit scope, System Admin business-data denial, Auditor audit-only access, Member assigned-task restrictions and ordinary transitions, Project Manager scope, department-only denial, cross-project access and non-disclosure, assignment alias, task parent-project resolution, dashboard aggregation, project listing, audit reads, CSRF and audit/workflow regression risks. Check missing/invalid roles and changes to shared policy callers where relevant. Cite file and line for concrete findings and say which criteria are not verified.

## Test evidence and limits
OpenCode run `2026-11-01T12-21-05-verifier-chpmis-017-scoped-independent-authorizat-fe0e` recorded all six assigned checks at exit 0: focused pytest 28 passed, auth policy 11 passed, full backend 136 passed/2 skipped, scoped Ruff and format passed, `git diff --check` empty. Its combined diff was truncated and an unlisted echo was denied. The source follow-up read seven diffs but had an unlisted command/denial deviation and supplied no substantive verdict. Owner accepted the six observed check results as test evidence and assigned the missing independent source review to this card; do not label either OpenCode process a clean verifier pass. This task is read-only; do not rerun or add tests unless explicitly needed and report any missing evidence.

## Definition of Done and result
Provide a criterion-by-criterion assessment, findings with priority P1/P2/P3, file:line, impact and correction direction, and a clear `APPROVED` or `CHANGES_REQUESTED` verdict. Report evidence gaps as `NOT_VERIFIED`; do not approve if a P1/P2 remains unresolved or a required review cannot be performed. End via the role card lifecycle with the verdict, evidence and limits. Coordinator updates task files and ledger.
