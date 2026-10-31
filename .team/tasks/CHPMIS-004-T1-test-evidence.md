# Task Pack — CHPMIS-004-T1 Independent Test Evidence

## Task ID and role
- Task ID: CHPMIS-004-T1
- Role: Hermes Tester / Verifier, independent from Worker.
- Parent: CHPMIS-004.
- Status: READY TO DISPATCH — Worker handoff received; implementation acceptance is pending independent evidence.

## Objective and authority
Independently rerun the verification commands already defined in `.team/tasks/CHPMIS-004-project-task-workflow.md` and examine the existing tests against AC-06–AC-10 and AC-12 project/task scope. This is a read-only task: do not edit, generate, or delete product files, test files, documentation, or implementation. Do not repair failures; report scoped findings.

## Required context
Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, the CHPMIS-004 task pack, accepted Human Gate decisions in `OPEN_QUESTIONS.md`, relevant role/security/data/workflow docs, and the Worker card/run report before testing. Inspect `git status` and preserve the dirty baseline.

## Verification commands
Use only scripts already present in repository and the CHPMIS-004 task pack. Run and report exact command, summary, and exit code:
- `.venv/Scripts/python -m pytest -v`
- `.venv/Scripts/ruff.exe check .`
- `.venv/Scripts/python -m alembic upgrade head --sql`
- `.venv/Scripts/python -m alembic downgrade 0004_projects_tasks_audit:0003_system_admin_requests --sql`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --run`
- `npm --prefix frontend run build`

If any command is absent or fails for an environmental reason, record `NOT_VERIFIED` with evidence; do not install dependencies, start Docker, contact providers, or access production.

## Test review matrix
- AC-06: PM project creation; explicit membership list/read; no deletion path.
- AC-07: in-scope PM membership grant/reassignment, target validation, System Admin without project membership denied.
- AC-08: project-scoped task create/assign, assigned-member validation, unknown/cross-project fail-closed behavior.
- AC-09: exact approved state transitions, role checks, terminal/cancel/reopen constraints.
- AC-10: guessed/cross-scope reads and writes neither disclose protected records nor mutate data.
- AC-12 project/task: event allowlist/minimization and same-transaction rollback on audit failure.
- Migration: additive/reversible, restrictive project/task references, no project delete or global audit read.
- Synthetic fixtures only; no identifying or real agency data.

## Prompt template
- Source: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, retrieved 2026-10-30: https://prompts.chat/prompts/cmmx34zl7000vil04rm2wl8yl_test-engineer-agent-role
- Modernized role prompt: “Apply the Test Engineer Agent Role to CHPMIS-004-T1 as an independent read-only verifier. Follow this task pack and the approved CHPMIS-004 task pack. Inspect existing tests and map observed coverage to each listed acceptance criterion; rerun only the listed repository commands. Do not create the template’s TODO file, add tests, modify any files, or repair failures: the charter assigns Tester evidence/reporting only. Report exact outputs and exit codes, uncovered criteria, and `NOT_VERIFIED` environmental limits. Finish with `kanban_complete(result=...)` or `kanban_block(reason=...)`; do not self-approve implementation.”

## Definition of Done
Record observed commands/results, AC mapping, gaps/findings and infrastructure limits on the Hermes card and in the task ledger. No files other than this task pack and ledger may be modified by the coordinator; Tester makes no file changes.


## Hermes card contract

ROLE: tester (read-only verification)
Work only inside this task's workspace.
1. Read the task pack, charter, ledger, approved decisions, and implementation summary before testing.
2. Inspect the existing implementation/tests; make no file changes and do not repair failures.
3. Run only the repository commands listed in the task pack; report exact command, summary, and exit code.
Finish with exactly one of:
- kanban_complete(result=acceptance trace, exact evidence, gaps, and NOT_VERIFIED limits)
- kanban_block(reason=why verification cannot proceed)

--- REQUIREMENT ---
Follow `.team/tasks/CHPMIS-004-T1-test-evidence.md` exactly. This is an independent, read-only verification of CHPMIS-004. Map existing test evidence to AC-06–AC-10 and AC-12, report untested criteria and environment limits. Do not create files or modify the working tree.
