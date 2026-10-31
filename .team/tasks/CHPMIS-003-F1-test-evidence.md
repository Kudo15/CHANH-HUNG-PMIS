# Task Pack — CHPMIS-003-F1 Independent Test Evidence

## Task and role
- Task ID: CHPMIS-003-F1-T1
- Role: independent Tester / read-only Verifier
- Status: READY TO DISPATCH
- Target Worker card/session: `t_5b6a5d8c` / `20261030_094108_d81b52`

## Scope and acceptance
Independently verify the implementation for CHPMIS-003-F1 against `.team/tasks/CHPMIS-003-F1-auth-security-remediation.md`. Do not edit code, tests, acceptance, ledger, or task docs. Inspect `git status` and the changed files, then run the repository's assigned verification commands from `backend/`:
- `.venv/Scripts/python -m pytest -v`
- `.venv/Scripts/ruff.exe check .`
- `.venv/Scripts/alembic.exe upgrade head --sql`
- `.venv/Scripts/alembic.exe downgrade 0003_system_admin_requests:0002_auth_foundation --sql`

Report exact commands, outputs, and exit codes. Verify test coverage includes signed/tampered tokens, wrong claims/nonce, fixed redirect, expired-state boundary, two-person role grant/revoke, no body-selected approver, self-approval/replay rejection, and durable request history. Actual IdP, remote JWKS, PostgreSQL runtime, Docker/HTTP-only login remain `NOT_VERIFIED` unless exercised without external/production access. Do not access a real IdP or install packages.

## Prompt template
- Library: prompts.chat via `.agents/skills/prompt-lookup`.
- Template: **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, retrieved 2026-10-30 and adapted read-only.
- Modernized prompt: “Independently verify CHPMIS-003-F1 only. Inspect the diff and task pack, preserve all files, and run the four listed commands from backend. Report exact results and exit codes; check that the specified security regressions are covered. Do not edit anything or install dependencies. Distinguish local evidence from NOT_VERIFIED provider/runtime behavior. Finish with PASS, FAIL, or NOT_VERIFIED per criterion.”

## DoD
- Read-only independent evidence covers all four commands and security regression criteria.
- Exact outcomes and remaining NOT_VERIFIED items are reported for the ledger.
