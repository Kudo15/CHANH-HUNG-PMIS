# Task Pack — CHPMIS-003-T1 Independent Test Evidence

## Task ID and execution role
- Task ID: CHPMIS-003-T1
- Role: Independent Tester / Hermes Verifier
- Status: READY — Worker card `t_73af3098` is in review.

## Context and objective
Independently run and inspect the CHPMIS-003 authentication/session/authorization tests. Verify the approved local-first-slice policy and report evidence. This is a read-only test task: do not edit or add product code/tests, do not repair failures, and do not create a generic `TODO_test-engineer.md` file.

## Files in scope
- Read-only review of auth-related files under `backend/app/**`, `backend/alembic/versions/**`, `backend/tests/**`, and the CHPMIS-003 task pack.
- No file writes. Test/cache artifacts may be produced by the repository's existing commands only.

## Traceability
- Mission §§4, 6; AC-03, AC-05, AC-10 as applicable.
- Approved HG1/HG2 in `OPEN_QUESTIONS.md` and `docs/security/SECURITY_MODEL.md`.
- Worker card: Hermes `t_73af3098`.

## Acceptance criteria
- [ ] Run backend tests and Ruff independently; report exact commands, output summary, and exit codes.
- [ ] Run the repository-supported offline Alembic upgrade/downgrade validation independently; report exact commands and exit codes.
- [ ] Inspect OIDC signature/claim validation (issuer, audience, expiry, nonce, state), fail-closed behavior, session cookie flags/CSRF/rotation/revocation/timeouts, and deprovisioning.
- [ ] Inspect deny-by-default role and project-scope checks, System Admin business-data isolation, no self-grant, distinct second-admin approval, and absence of project/task schema or an initial-admin bootstrap.
- [ ] Treat actual IdP connectivity, Docker/PostgreSQL runtime, and browser login over current HTTP-only local Compose as `NOT_VERIFIED` unless independently evidenced.
- [ ] Do not make implementation changes. Open scoped findings/follow-up task recommendations for failures.

## Prompt template
- Library: prompts.chat via `.agents/skills/prompt-lookup`.
- Template: **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, https://prompts.chat/prompts/cmmx34zl7000vil04rm2wl8yl_test-engineer-agent-role
- Retrieved full template on 2026-10-30. Modernized for this read-only verification: inspect acceptance trace and existing tests, execute focused and full repository checks, independently probe security-negative cases where commands permit, capture exact results, and report gaps. The source template's test-writing/TODO-file, coverage percentage, and mutation-score instructions are excluded because this assigned Tester is read-only and the project has no approved numeric coverage threshold.

## Verification commands
- `py -3.13 -m pytest -q` from `backend/`; if the Windows launcher is unavailable, report that and run the existing project virtualenv's `python -m pytest -q` as the equivalent, recording the exact executable and exit code.
- `py -3.13 -m ruff check .` from `backend/`; if unavailable, use the existing `.venv/Scripts/ruff.exe check .` and record exact output/exit code.
- Offline Alembic upgrade and downgrade SQL generation for the new revision. Identify the exact commands from the repository/task pack and report exit codes. No Docker installation or real PostgreSQL service.

## Risks and boundaries
- Never use real IdP configuration, real identities, agency data, secrets, external network calls, or production.
- The Tester cannot turn an unverified result into PASS and cannot silently fix implementation.

## Definition of Done
- Read-only checks and scoped security inspection are evidenced, all gaps are listed, and the ledger records observed harness/model/provider/profile/effort only.
