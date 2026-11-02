# CHPMIS-018-F1 — Reproduce Concurrent Task Status Lost Update

## Task identity

- **Task ID:** CHPMIS-018-F1
- **Role:** PostgreSQL Test Worker (test-only); then independent Tester/Reviewer
- **Status:** READY — mission §6 requires a task lost-update reproduction; no product fix is authorized by this pack.
- **Trace:** mission §6; approved Human Gate 3 transition graph; existing CHPMIS-018 task consistency finding.

## Objective

Deterministically reproduce two concurrent Project Manager status transitions for the same task when both requests read the same prior state. Confirm whether both are accepted and both audit entries use a stale `in_progress` before-state.

## Scope and boundaries

- Only `backend/tests/test_postgresql.py` may change; append `.team/tasks/CHPMIS-018-F1-worker-report.md`.
- Test-only. Do not change `backend/app/`, models, migrations, schema, permission rules, transition graph, API responses, or workflow behavior.
- Use a fresh migrated synthetic PostgreSQL database with an `018_f1` task namespace in its name. Preserve every database; no drop/reset/cleanup.
- Seed synthetic Project Manager, explicit project membership, one project, one in-progress task, session, and audit data only.
- If the test demonstrates stale concurrent acceptance, report exact RED evidence and stop. Request a separately scoped Human Gate review for any row lock/optimistic concurrency fix; do not implement it here.

## Required reproduction

1. First reproduce on the live synthetic service before making file changes. If a scratch harness is needed, use only the task's temporary test process, preserve all records, and record its exact command/output.
2. Force two distinct concurrent PM requests for the same task to reach the `SELECT Task` operation together, using a bounded SQLAlchemy event barrier before query execution (or an equally deterministic PostgreSQL-only technique). A timer-only race is insufficient. Always remove event listeners in `finally`.
3. Request transitions `in_progress → done` and `in_progress → cancelled`, both allowed for a PM by the existing HG3 graph. Safe serialized behavior under current API semantics is one 200 and one 400 invalid-transition response; exactly one transition audit event; the final status equals the winning request. If both return 200 and both record `before.status == in_progress`, record the lost update and stop without a product fix.
4. Preserve existing same-request admin-approval concurrency test unchanged.

## Verification

From `backend/`, with process-local synthetic loopback PostgreSQL settings:

- `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k concurrent_task_transition_serialized`
- `.venv\Scripts\ruff.exe check tests/test_postgresql.py`
- `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py`
- From repository root: `git diff --check -- backend/tests/test_postgresql.py .team/tasks/CHPMIS-018-F1-worker-report.md`

Report exact output, exit, skip status, database name, and preservation evidence. Do not commit. A PostgreSQL skip is NOT_VERIFIED.

## Prompt template

- Real template retrieved via installed prompt-lookup: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as a test-only CHPMIS-018 PostgreSQL Worker. First reproduce two concurrent PM transitions from the same `in_progress` state to `done` and `cancelled` using a deterministic bounded barrier before the task SELECT. Modify only `backend/tests/test_postgresql.py` and append your report. Use a fresh synthetic `018_f1` database and preserve it; never drop/reset data or inspect/print credentials. Preserve existing auth-concurrency tests. If both transitions are accepted with stale audit before-values, record RED and stop; do not change app, model, schema, transition graph, or API behavior. Run the assigned checks and report exact results/exits/skips. Request independent review; do not commit.”

## Definition of Done

- A deterministic live PostgreSQL reproduction covers two distinct task-transition requests from one prior state.
- The exact observed HTTP, task-state, and audit-state outcomes are recorded.
- No product code/schema changes occur; any reproduced defect stays blocked for a separate approved fix.
- Independent review assesses the test-only diff.

## Hermes card closing contract

ROLE: worker (test-only). Work only in this task's workspace. Keep Worker, Tester, Reviewer serialized. Finish with exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include RED result, commands, output/exits, skip status, database name, requirement trace, and limits. Do not commit.
