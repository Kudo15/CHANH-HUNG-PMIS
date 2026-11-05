# CHPMIS-018-F2 — Serialize task status decisions

## Identity and authorization

- **Task ID:** CHPMIS-018-F2; **roles:** OpenCode Worker → OpenCode independent Tester and Reviewer; Coordinator owns synthetic runtime/evidence.
- **Status:** COMPLETE — owner accepted the Coordinator's final six checks plus independent R2 review as the scoped substitute for unavailable Tester executions. The OpenCode Tester's six checks remain NOT_VERIFIED: command 1 was denied and commands 2–6 were not attempted. F1-T1 remains BLOCKED.
- **Trace:** CHPMIS-018-F1 and mission §6; approved local task transition graph HG3; `.team/tasks/CHPMIS-018-F2-task-transition-concurrency-proposal.md`.
- **Owner decisions 2026-11-03:** Approved the proposal's serialized decision, existing 400 semantics, atomic truthful audit and two-file product/test scope. Explicitly accepts the recorded Worker RED as starting evidence while F1-T1 remains BLOCKED / independently NOT_VERIFIED. Separately approved one fresh PostgreSQL 17 synthetic container on a random loopback port, with a process-generated synthetic password supplied via environment to OpenCode; preserve its container, volume, and test databases. No role-permission change or F1-T1 exception is approved.

## Required session start

Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this task pack, the approved F2 proposal, the F1 Worker report, `docs/MISSION.md`, `ACCEPTANCE.md`, and relevant task/workflow code before acting. Report the required reads. Preserve all dirty work.

## Worker scope and objective

- Modify only `backend/app/projects/service.py` and `backend/tests/test_postgresql.py`; append only `.team/tasks/CHPMIS-018-F2-worker-report.md` for the handoff.
- Serialize the status decision and update for one task in the existing transaction using a PostgreSQL row lock, with refreshed ORM state before applying the existing graph. Preserve project authorization/non-disclosure, roles, 400 response behavior, and atomic status/audit writes. Do not change schemas, migrations, dependencies, global authorization or transition graph.
- For concurrent `in_progress → done` and `in_progress → cancelled`, one request must succeed and one return 400; exactly one transition audit entry records the actual before/after state, and final status matches the winner. If transitions are both valid sequentially under the existing graph, keep that graph and accurate audit values.
- Write the lock-compatible PostgreSQL concurrency regression first. The F1 two-stage barrier deliberately proves the old race and cannot pass under a row lock; adapt/replace that task-owned test to avoid a barrier deadlock while preserving the F1 report and all existing admin approval tests. Use bounded synchronization and verify actual outcomes/state/audit; no timer-only race. The owner explicitly accepted the recorded F1 RED as entry evidence. If a live context is supplied, run the new regression before and after implementation and report its observed result honestly.
- Use only process-local synthetic PostgreSQL settings supplied to the Worker; do not print or inspect values, use other services, start/stop containers, alter role permissions, reset/drop databases, clean other artifacts, stage, commit, push or deploy. If settings are absent or test commands cannot execute, stop and report `BLOCKED / NOT_VERIFIED` before product edits. Fresh task-created synthetic databases must be preserved.

## Verification

From `backend/`, with the task's authorized synthetic live PostgreSQL context:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k concurrent_task_transition_serialized`
2. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
3. `.venv\Scripts\python.exe -m pytest -q tests/test_tasks_workflow.py tests/test_projects.py`
4. `.venv\Scripts\ruff.exe check app/projects/service.py tests/test_postgresql.py`
5. `.venv\Scripts\ruff.exe format --check app/projects/service.py tests/test_postgresql.py`

From the repository root: `git diff --check -- backend/app/projects/service.py backend/tests/test_postgresql.py .team/tasks/CHPMIS-018-F2-worker-report.md`. Report command output, exit code, skip count, synthetic database names, and limits. A skipped live test is NOT_VERIFIED.

## Prompt template

Retrieved via the installed `prompt-lookup` skill: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template. Modernized task: “Act as the bounded Python/FastAPI/SQLAlchemy Worker. Use the owner-accepted F1 RED as starting evidence, then write a lock-compatible live PostgreSQL regression before implementing serialized task transitions and accurate atomic audit. Preserve the access rules, approved graph, HTTP behavior and allowed files. Run the exact checks, disclose skips and failures, preserve synthetic databases, and report for independent OpenCode review without committing.” The template's generic README instruction does not expand this allowlist.

## Definition of Done

- Owner-approved behavior and allowed files only; live concurrency regression and related checks are recorded with exact exits and no relevant skips.
- Worker report states requirement trace, commands/results, database preservation, and all limitations.
- Independent OpenCode Tester and separate OpenCode Reviewer assess the final changes; neither permission denial nor missing test evidence is represented as a pass.
- Coordinator updates `.team/ledger.md`, `TASKS.md`, and other status documents. F1-T1 remains BLOCKED unless its separate decision is changed.
