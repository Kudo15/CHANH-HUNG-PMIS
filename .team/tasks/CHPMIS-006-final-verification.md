# Task Pack — CHPMIS-006 Full Verification and Final Readiness

## Task ID and roles
- Task ID: CHPMIS-006
- Roles: Hermes Tester/QA and independent security-focused Reviewer.
- Status: COMPLETE — Tester card `t_4745e8e2` evidence complete; independent Reviewer `t_cd6ff3e9` APPROVED.
- Trace: `PLAN.md` Phase 3; mission §§5–6, 8; `ACCEPTANCE.md` AC-01–AC-15.

## Objective and authority
Run the complete repository-defined verification matrix read-only, map evidence to AC-01–AC-15, identify unresolved requirements and risks, and produce an independent final readiness review. Do not change product code, tests, CI, or acceptance claims. Report findings and propose scoped follow-up tasks; Coordinator records evidence and updates status. Real IdP E2E, remote CI, legal approval, and production readiness must not be claimed without evidence.

## Required context
Read `AGENTS.md`, `.team/CHARTER.md`, this task pack, `.team/ledger.md`, `PLAN.md`, `ACCEPTANCE.md`, `OPEN_QUESTIONS.md`, relevant mission/security/roles/data/workflow docs, and CHPMIS-003/004/005 evidence. Inspect `git status` and preserve the dirty baseline.

## Tester commands
Use the repository's existing commands only. Record exact command, working directory, summary and exit code. Do not install packages, call production, or modify files.
- From `backend/`: `.venv/Scripts/python -m pytest -v`
- From `backend/`: `.venv/Scripts/ruff.exe check .`
- From `backend/`: `.venv/Scripts/ruff.exe format --check .`
- From `backend/`: `.venv/Scripts/python -m alembic upgrade head --sql`
- From `backend/`: `.venv/Scripts/python -m alembic downgrade 0004_projects_tasks_audit:0003_system_admin_requests --sql`
- From repository root: `npm --prefix frontend run lint`
- From repository root: `npm --prefix frontend run test -- --run`
- From repository root: `npm --prefix frontend run build`
- From repository root: `npm --prefix frontend run test:e2e` (Playwright config starts Vite on `127.0.0.1` only; confirm existing config before running).
- From repository root, with process-local synthetic values only: `$env:POSTGRES_PASSWORD='synthetic_ci_only'; $env:DATABASE_URL='postgresql+psycopg://pmis_dev:synthetic_ci_only@db:5432/pmis_dev'; docker compose config --quiet`.

If Docker/Compose is unavailable, the test DB is skipped, or SSO provider/browser support is absent, record `NOT_VERIFIED` and the exact evidence. Do not access real IdP, networks, production, or real data. Do not start containers unless an existing approved test instruction requires it; configuration-only validation is safe.

## Acceptance matrix
- AC-01: local stack configuration and localhost-only bindings; runtime remains separate evidence from static config.
- AC-02–04: health/readiness, empty/additive migration safety, repeatable checks/CI configuration; remote CI remains `NOT_VERIFIED` unless run.
- AC-05: signed-token/session/authz foundation tests; actual external IdP/JWKS sign-in remains `NOT_VERIFIED`.
- AC-06–09: project/task creation, assignment, scoped access and approved state transitions evidence from CHPMIS-004.
- AC-10: cross-project isolation verified; broader acceptance remains `PARTIAL` until the record explicitly states department membership alone grants no access and evidence is adequate. Do not overstate this criterion.
- AC-11–13: scoped dashboard, audit write/read, approved reader authorization and safe audit visibility evidence from CHPMIS-004/005.
- AC-14: full browser journey requires actual approved IdP and session transport. No fake login; keep `NOT_VERIFIED` if the provider remains unselected.
- AC-15: synthetic-only fixtures, secret hygiene, no external AI integration; inspect only candidate Git files/config without exposing values.

## Independent Reviewer scope
Perform spec-first and security review of the complete scoped implementation and acceptance evidence. Check cross-project isolation, deny-by-default auth, audit atomicity/allowlists and read access, workflow boundaries, localhost binding, secret handling, migrations, and test results. Do not modify files. Every required finding must include P1/P2/P3, exact file:line, impact, and correction direction. End with `APPROVED` or `CHANGES_REQUESTED`; this is not legal/compliance or production certification.

## Prompt templates
- Tester: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, retrieved/adapted in `.team/tasks/CHPMIS-005-T1-test-evidence.md`; adapt to read-only full matrix and no TODO file.
- Reviewer: prompts.chat **Senior Code Reviewer (severity-ranked)**, ID `cmv9n79m30005ku060pzornri`, retrieved/adapted in `.team/tasks/CHPMIS-005-R1-security-review.md`; focus on whole-slice security and acceptance evidence.

## Definition of Done
- Tester records each exact command, result, exit code, AC mapping, failures, and `NOT_VERIFIED` limits; makes no file changes.
- Reviewer records independent spec-first/security verdict and actionable findings; makes no file changes.
- Coordinator updates `ACCEPTANCE.md` only to evidence-supported statuses and records the final local-readiness summary in `.team/ledger.md`.
- Actual IdP, live PostgreSQL/Compose runtime, remote CI, browser SSO, and any criterion lacking executed evidence remain `NOT_VERIFIED`.

## Final evidence
- Tester card `t_4745e8e2`, run #21, session `20261030_114102_badd89`: nine runnable commands passed exit 0 (backend pytest 61 passed/1 skipped, Ruff check/format, offline Alembic upgrade/downgrade; frontend lint, Vitest 6 passed, build, Playwright shell E2E). Docker Compose config returned exit 127 because Docker is not installed. Tester made no file changes.
- Independent Reviewer card `t_cd6ff3e9`, run #22, session `20261030_114436_64162f`: `APPROVED`, no P1/P2/P3 findings.
- AC status: PASS 02, 06–09, 11–13, 15; PARTIAL 10; NOT_VERIFIED 01, 03–05, 14. AC-04 additionally awaits remote CI; AC-05/14 await actual IdP/browser SSO.
- Readiness is local-first-slice only, not production/legal certification.


## Hermes Tester card contract

ROLE: tester (read-only full-slice verification)
Work only inside this task's workspace.
1. Read the task pack, charter, ledger, plan, acceptance, approved decisions, and prior task evidence.
2. Run only verification commands listed in the task pack; do not install dependencies or modify files.
3. Report each command, exact result and exit code, then map evidence/gaps to AC-01–AC-15.
Finish with exactly one of:
- kanban_complete(result=full evidence matrix, exact commands, gaps and NOT_VERIFIED limits)
- kanban_block(reason=why final verification cannot proceed)

--- REQUIREMENT ---
Follow `.team/tasks/CHPMIS-006-final-verification.md` as an independent read-only Tester. Do not update ACCEPTANCE.md or modify files. Do not fake IdP/browser evidence.


## Hermes independent Reviewer card contract

ROLE: reviewer (independent full-slice security review)
Work only inside this task's workspace.
1. Read the final verification task pack, charter, ledger, plan, acceptance matrix, and Tester report.
2. Review the evidence and current scoped implementation/config against requirements; do not run unlisted commands or edit files.
3. Assess each AC without overstating evidence; examine unresolved AC-10/14 and Docker/IdP gaps.
Finish with exactly one of:
- kanban_complete(result=APPROVED or CHANGES_REQUESTED, full acceptance evidence review and findings)
- kanban_request_changes(reason=concrete required findings)
- kanban_block(reason=why review cannot proceed)

--- REQUIREMENT ---
Perform the independent security-focused review defined in `.team/tasks/CHPMIS-006-final-verification.md`. Review read-only. Every required finding must include P1/P2/P3, file:line, impact, and correction direction. Do not certify legal/compliance or production readiness.
