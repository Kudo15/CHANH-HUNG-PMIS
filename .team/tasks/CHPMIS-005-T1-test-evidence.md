# Task Pack — CHPMIS-005-T1 Independent Test Evidence

## Task ID and role
- Task ID: CHPMIS-005-T1
- Role: Hermes Tester / Verifier, independent from Worker.
- Parent: CHPMIS-005; Worker implementation card `t_0c1b86d4`.
- Status: READY TO DISPATCH — Worker handoff complete.

## Objective and authority
Independently rerun the repository verification commands defined by `.team/tasks/CHPMIS-005-dashboard-audit-read.md`, inspect existing tests against AC-11–AC-13, and report exact results. Read-only only: do not edit, add, generate, or delete any files; do not repair failures. Tester evidence is not implementation approval.

## Required context
Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, CHPMIS-005 and CHPMIS-004 task packs, accepted HG2–HG4 decisions, relevant API/security/roles/workflow docs, and the Worker card summary. Inspect `git status` before testing and preserve the dirty baseline.

## Commands
Use only existing repository scripts and report exact commands, output summaries and exit codes:
- From `backend/`: `.venv/Scripts/python -m pytest -v`
- From `backend/`: `.venv/Scripts/ruff.exe check .`
- From `backend/`: `.venv/Scripts/python -m alembic upgrade head --sql`
- From `backend/`: `.venv/Scripts/python -m alembic downgrade 0004_projects_tasks_audit:0003_system_admin_requests --sql`
- From repo root: `npm --prefix frontend run lint`
- From repo root: `npm --prefix frontend run test -- --run`
- From repo root: `npm --prefix frontend run build`

Do not install dependencies, start Docker, contact a real IdP, or access production. PostgreSQL test skip and browser/IdP gaps remain `NOT_VERIFIED`.

## Acceptance test matrix
- AC-11: project membership applied before state and overdue counts; all approved statuses counted; no unauthorized project leaks through summary, totals or list.
- AC-12 read portion: only safe audit metadata/allowlisted context returned; read-only access and no mutation.
- AC-13: assigned PM/Auditor access; Member, unrelated System Admin, guessed/cross-project, inactive and unauthenticated requests fail closed without revealing protected records.
- Cursor: stable order, page size cap, tampered/cross-project cursor rejected; no page crosses scope.
- Overdue: deterministic due boundary, null date, terminal done/cancelled exclusion, blocked remains outstanding.
- UI uses cookie-authenticated protected APIs and does not simulate identity/authorization with a client-side role selector or fixture data.

## Prompt template
- Source: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, retrieved previously and referenced in CHPMIS-004-T1: https://prompts.chat/prompts/cmmx34zl7000vil04rm2wl8yl_test-engineer-agent-role
- Modernized Tester prompt: “Apply the Test Engineer Agent Role as an independent read-only verifier for CHPMIS-005-T1. Follow this task pack and CHPMIS-005 acceptance matrix. Inspect tests and map observed coverage to AC-11–AC-13; rerun only listed repository commands. Do not create the template’s TODO file, add tests, modify any files or fix failures. Report exact commands, summaries, exit codes, uncovered criteria, and all `NOT_VERIFIED` limits. Finish with `kanban_complete(result=...)` or `kanban_block(reason=...)`; do not self-approve.”

## Definition of Done
Hermes report includes exact evidence and AC trace, tests run read-only, uncovered cases and environment gaps. No Tester file changes.


## Hermes Tester card contract

ROLE: tester (read-only verification)
Work only inside this task's workspace.
1. Read the task pack, charter, ledger, approved decisions, and Worker handoff before testing.
2. Inspect existing tests; make no file changes and do not repair failures.
3. Run only listed repository commands; report exact command, summary, and exit code.
Finish with exactly one of:
- kanban_complete(result=AC trace, evidence, uncovered criteria, NOT_VERIFIED limits)
- kanban_block(reason=why independent verification cannot proceed)

--- REQUIREMENT ---
Follow `.team/tasks/CHPMIS-005-T1-test-evidence.md` exactly. Independently verify AC-11–AC-13 and report evidence. No files may be modified.
