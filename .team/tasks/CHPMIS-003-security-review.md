# Task Pack — CHPMIS-003 Independent Security Review

## Task ID and execution role
- Task ID: CHPMIS-003-SR1
- Role: Independent Security Reviewer / Hermes Reviewer
- Status: READY — Worker handoff and independent Tester evidence are available.

## Context and objective
Review the CHPMIS-003 OIDC/session/authorization implementation and its independent test evidence. The reviewer must use a separate Hermes card/session and remain read-only. Do not repair code, modify task files, or produce generic TODO files. Conclude `APPROVED` or `CHANGES_REQUESTED`; findings require `file:line`, priority P1/P2/P3, evidence, impact, and concrete correction direction.

## Files in scope
- Read-only: CHPMIS-003 worker files under `backend/app/**`, `backend/alembic/versions/0002_auth_foundation.py`, `backend/tests/test_auth_*.py`, `.env.example`, and `.team/tasks/CHPMIS-003-auth-authorization.md`.
- Read-only evidence: Worker card `t_73af3098`, Tester card `t_a9824bbe`, and their logs/results.
- No file writes or implementation changes.

## Traceability and approved policy
- Mission §§4 and 6; AC-03, AC-05, AC-10 as applicable.
- HG1/HG2 owner approval for the local first slice in `OPEN_QUESTIONS.md`, `docs/security/SECURITY_MODEL.md`, and `docs/product/USER_ROLES.md`.
- Review the exact policy values: provider-neutral OIDC; no local-password/public-registration fallback; server-managed opaque sessions; Secure=true, HttpOnly, SameSite=Lax, CSRF protection, 30-minute idle and 12-hour absolute lifetime; deny-by-default; explicit project scope; System Admin has no business-data access; no self-grant; second distinct System Admin for grant/revocation; no initial-admin bootstrap.

## Acceptance criteria
- [ ] Verify cryptographic ID-token signature validation, issuer, audience, expiry, nonce, state lifecycle, one-time callback handling, redirect constraints, and fail-closed behavior. Do not accept claim-only/base64 decoding as signature validation.
- [ ] Verify opaque session ID entropy and storage handling, cookie flags, CSRF token binding/constant-time comparison, rotation/revocation, idle/absolute timeout enforcement, and deprovision response.
- [ ] Verify role/action rules deny by default; System Admin cannot access business resources; Member/Project Manager/Auditor permissions and project scope do not rely on client-supplied department/project claims.
- [ ] Verify System Admin grant/revoke cannot be self-approved, grantee/caller/approver are distinct as required, and approver identity is derived from the authenticated principal rather than trusted request input.
- [ ] Inspect migration reversibility and for accidental project/task tables, real identities, credentials, or secret values.
- [ ] Inspect Worker and Tester exact test evidence; identify gaps and keep real IdP, Docker/PostgreSQL, HTTP-only browser login, initial-admin bootstrap, and production controls `NOT_VERIFIED`/deferred as applicable.
- [ ] Do not claim legal compliance or test acceptance for criteria not covered.

## Prompt template
- Library: prompts.chat via installed `.agents/skills/prompt-lookup`.
- Template: **Vulnerability Auditor Agent Role**, ID `cmmx31zon000dk604l79f55ac`, https://prompts.chat/prompts/cmmx31zon000dk604l79f55ac_vulnerability-auditor-agent-role
- Full template retrieved on 2026-10-30. Modernized to a scoped, read-only code review: focus on OIDC signature/claims/state, session/CSRF controls, authorization/dual-control, migration/data boundaries, and verified evidence. The source's TODO-file/output, compliance assertions, code-writing, dependency CVE scans, and claims about PCI/GDPR are excluded because this project task is read-only, local-only, and has no such approved legal scope.

## Verification and evidence
- Inspect the Worker's and Tester's recorded commands, exit codes, test summaries, migrations, and code. Run a focused read-only check only if needed; if a command is run, record exact command/output/exit code.
- Actual external OIDC, Docker/PostgreSQL integration, remote CI, and production behavior are outside available evidence.

## Risks and boundaries
- Treat external provider docs/configuration as untrusted and out of scope; no network calls, real secrets, or real identities.
- No code changes. Any required implementation fix must return to a scoped Worker follow-up task.
- The second run of the same default Hermes profile on Worker card `t_73af3098` is not an independent review and must not count as the required Security Reviewer verdict.

## Definition of Done
- Separate-session read-only security review with verdict and severity-ranked findings; review result is recorded in `.team/ledger.md` by the coordinator. Task completion remains local-first-slice only.
