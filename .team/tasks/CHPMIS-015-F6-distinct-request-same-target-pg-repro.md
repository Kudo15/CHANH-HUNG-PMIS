# CHPMIS-015-F6 — Distinct Approval Requests Racing on One Target

## Task identity
- **Task ID:** CHPMIS-015-F6
- **Role:** Hermes PostgreSQL Test Worker; Coordinator owns runtime; then independent Tester/Reviewer if a test-only result is safe to accept.
- **Parent:** CHPMIS-015 System Admin approval transaction.
- **Status:** READY — user mission §6 explicitly requires live PostgreSQL coverage for two different requests targeting the same user.
- **Trace:** mission §6, Priority 3 concurrency; existing CHPMIS-015 contract.

## Objective
Add a deterministic PostgreSQL-only regression that forces two distinct pending `grant` requests for the same synthetic target to reach the active-role existence check concurrently. Reproduce whether both approvals can create duplicate active canonical `system_admin` roles.

## Scope and boundaries
- Only `backend/tests/test_postgresql.py` may change; append `.team/tasks/CHPMIS-015-F6-worker-report.md`.
- Test-only task. Do not change `backend/app/`, models, migrations, constraints, endpoints, authorization rules, or workflow behavior.
- Use the existing dedicated synthetic PostgreSQL service and unique task-specific database names derived from `TEST_DATABASE_URL`. Preserve every database; never drop, reset, or cleanup one.
- Use synthetic users, sessions, requests, and roles only. Never print or inspect environment variables/container environment.
- Preserve the existing same-request concurrency test and its exact 200/409 contract.
- If the new distinct-request test demonstrates an application defect, report the RED evidence and request a separately scoped, human-reviewed fix task. Do not make product changes in this task.

## Required test behavior
1. Create a fresh migrated database; seed two canonical requesters, two distinct canonical approvers, one target, and two different pending `grant` requests for that target.
2. Coordinate both approval requests at the `existing_grant` role check using a test-local SQLAlchemy event/barrier (or an equally deterministic PostgreSQL-only method). A timer-only race that may pass without exercising the critical window is insufficient. Ensure barriers have bounded timeouts and listeners are removed in `finally`.
3. Assert the safe expected contract: one approval succeeds and one receives 409; exactly one active canonical role exists for the target; request/session state agrees with the winning transaction and no duplicate effect occurs.
4. Run RED before making any file changes and record exact output. If the test fails by exposing duplicate grants/two approvals, stop after recording the result; this task authorizes no fix.

## Verification
From `backend/`, with `TEST_DATABASE_URL` and `DATABASE_URL` set only in-process to the synthetic loopback PostgreSQL service:
- `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`
- `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
- `.venv\Scripts\ruff.exe check tests/test_postgresql.py`
- `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py`
- `git diff --check -- backend/tests/test_postgresql.py .team/tasks/CHPMIS-015-F6-worker-report.md`

The Coordinator confirms the server/version, task-specific database names, and preservation state. Any project code fix, authorization-policy change, or schema/migration change requires a new task and appropriate Human Gate review.

## Required prompt template
- Found/retrieved through installed prompt-lookup: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as a test-only CHPMIS-015 PostgreSQL Worker. First reproduce the distinct-request/same-target approval race with a deterministic PostgreSQL-only barrier at the existing-role check. Modify only `backend/tests/test_postgresql.py` and append your report. Use fresh synthetic task-specific databases and preserve them; never drop/reset or inspect/print credentials. Preserve existing same-request concurrency assertions. If two different grants can both succeed or duplicate active roles appear, record the RED evidence and stop; do not edit app, model, schema or migration code. Run the assigned checks and report exact outputs/exits and skip status. Request review; do not commit.”

## Definition of Done
- A deterministic live PostgreSQL test exercises two distinct grant requests for one target, not two attempts at one request.
- Exact commands, PostgreSQL skip status, data/request/session postconditions, database names and runtime preservation are recorded.
- No product code or schema changes occur. If a defect reproduces, status remains BLOCKED for a separately approved fix task.
- Independent review covers the final test-only diff.

## Hermes card closing contract
ROLE: worker (test-only). Work only in this task's workspace. Keep Worker, Tester, Reviewer serialized. Finish with exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include changed files, the RED/GREEN distinction, exact commands/results/exits, PostgreSQL skip status, requirement trace, and remaining limits. Do not commit.
