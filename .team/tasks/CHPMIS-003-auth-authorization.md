# Task Pack — CHPMIS-003 Authentication and Authorization Foundation

## Task ID and execution role
- Task ID: CHPMIS-003
- Role: Hermes Worker (implementation) + independent Tester + Security Reviewer
- Status: CHANGES_REQUESTED by independent Security Reviewer — see CHPMIS-003-SR1 and remediation task CHPMIS-003-F1.

## Context
CHPMIS-002 created the React/Vite and FastAPI/PostgreSQL foundation. Its source remains in the current working tree as uncommitted changes, so a separate Git worktree would omit required baseline files. Run this task in the existing project directory, sequentially; do not clean, reset, stage, or overwrite unrelated pre-existing changes. Reviewer runs in a separate read-only Hermes session after the Worker and Tester finish.

Use synthetic identities and fixtures only. The exact organization OIDC provider is not selected and no real provider secrets/configuration may be added. Implement a provider-neutral OIDC boundary and test it with deterministic mocks; record actual-provider connectivity as `NOT_VERIFIED`. No network call to a real IdP is authorized.

## Approved decisions
See `OPEN_QUESTIONS.md` and `docs/security/SECURITY_MODEL.md` for the 2026-10-30 owner approval. Key requirements:
- OIDC SSO, no public self-registration or local-password fallback; IdP controls MFA and is authoritative for identity/account state/department membership.
- Server-managed opaque sessions in Secure, HttpOnly, SameSite=Lax cookies; CSRF protection; rotate on authentication/privilege changes; revoke on logout/deprovision; 30-minute idle and 12-hour absolute timeout.
- Deny by default; enforce permissions server-side on every request. Department membership alone grants no project access.
- System Admin: account/role configuration only, no implicit business-data access. Project Manager: actions in assigned projects. Member: read assigned projects and update only own assigned tasks. Auditor: read audit only in assigned projects; no global auditor.
- System Admin cannot self-grant; grants/revocations require a second existing System Admin. Initial two-admin nomination/provisioning is still open in `OPEN_QUESTIONS.md`; do not build a bootstrap bypass. CHPMIS-004 owns project membership persistence and project/task resources; CHPMIS-003 should define an authorization interface that can consume project scope without inventing project schema.
- Do not implement account bootstrap, real IdP integration, provider secrets, project/task schema, or business endpoints in this task. If a required identity/bootstrap detail prevents a safe implementation, report `BLOCKED` with the exact gap instead of adding a bypass.

## Objective
Implement and test the approved provider-neutral authentication/session boundary and reusable server-side authorization policy foundation so later project/task APIs can enforce the approved role and explicit project-scope rules.

## Files in scope
- Modify/create only auth-related files under `backend/app/**`, auth migrations under `backend/alembic/versions/**`, and auth tests under `backend/tests/**`.
- Modify `backend/requirements*.txt`, `backend/constraints.txt`, `.env.example`, or `README.md` only when strictly needed for the approved auth configuration and local synthetic test instructions.
- Frontend auth/sign-in files may be changed only if required for a working local first-slice sign-in shell; no project/task UI in this task.
- Forbidden: project/task/domain schema, project membership schema, task transitions, dashboard/audit endpoints, Compose/CI changes, real IdP config/secrets, real identities/departments/data, production/deployment, financial/legal policy, any unrelated cleanup.

## Traceability
- Mission §§2, 4, 6; `PLAN.md` Phase 2 Task 1; `TASKS.md` CHPMIS-003.
- `OPEN_QUESTIONS.md` approved HG1/HG2; `docs/security/SECURITY_MODEL.md`; `docs/product/USER_ROLES.md`; AC-03, AC-05–AC-10, AC-15 as applicable to auth boundaries.

## Acceptance criteria
- [ ] OIDC login/callback is provider-neutral, validates state/nonce and issuer/audience/signature/expiry as appropriate, and fails closed; tests use a deterministic mock, never a real IdP.
- [ ] No local password, public registration, or fallback identity path exists.
- [ ] Server-side opaque sessions satisfy approved cookie/CSRF/rotation/revocation/time-limit policy; cookies never expose bearer tokens to JavaScript.
- [ ] Authentication rejects missing, expired, revoked, deprovisioned, and invalid-claim sessions.
- [ ] Authorization functions enforce approved action/role rules, deny by default, deny department-only scope, and resolve task authorization through parent-project scope interface when applicable.
- [ ] System Admin does not imply business-data access; self-grant is denied; any privileged role-grant path requires a distinct second existing System Admin or remains unimplemented and reported as blocked.
- [ ] Positive and negative tests cover unauthenticated, wrong-role, cross-project, self-grant, second-admin, session/CSRF, and identity deprovision cases that are implementable within scope.
- [ ] No project/task schema or unrelated files changed. Migration is reversible and limited to auth/session/grant data.
- [ ] Exact verifier commands/results and all unverified provider/bootstrap items are recorded; independent Tester and Security Reviewer evidence is required before task completion.

## Verification commands and evidence
- Backend tests: `py -3.13 -m pytest -q` from `backend/`.
- Lint: `py -3.13 -m ruff check .` from `backend/`.
- Offline migration validation: use the exact repository-supported Alembic command identified by the Worker; do not claim PostgreSQL migration runtime evidence without Docker/PostgreSQL.
- Existing project commands: `npm test -- --run`, `npm run build`, and `npm run lint` from `frontend/` if frontend files change.
- Capture TDD RED and GREEN evidence, exact exit codes, and test output. Real OIDC provider, Docker/PostgreSQL, and remote CI remain `NOT_VERIFIED` if unavailable.

## Prompt template
- Library: prompts.chat via installed `.agents/skills/prompt-lookup`.
- Template: **Feature coding template**, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Retrieved full template on 2026-10-30. It asks a senior software engineer to implement a bounded feature, preserve language conventions, handle errors, test changes, update documentation, and report a commit summary.
- Modernized worker prompt: “Act as the backend authentication engineer implementing CHPMIS-003 in the supplied project task pack. Follow the approved HG1/HG2 decisions exactly. Work test-first: write focused negative/positive tests, show RED, implement the smallest secure change, then show GREEN and run the listed checks. Implement only provider-neutral OIDC and server-managed session/authz foundations; never call a real IdP, add secrets, invent a bootstrap bypass, or create project/task schema. Enforce CSRF, cookie flags, rotation/revocation/timeouts, deny-by-default, explicit project-scope lookup, admin self-grant denial, and second-admin separation. Preserve existing unrelated working-tree content, do not reset/clean, and do not modify out-of-scope files. Report exact changed files, commands/exit codes, RED/GREEN evidence, review blockers, and unverified real-provider/database behavior. Finish by requesting independent review; do not self-approve.”

## Risks, Human Gates, and boundaries
- Owner approval is limited to local first-slice development. No real identity provider, provider secret, production service, or real agency identity is approved.
- Initial System Admin bootstrap is intentionally excluded; do not create an automatic first-admin or self-promotion path. If testing or implementation requires such a path, stop and report the gap for a separate Human Gate.
- Human Gate does not certify compliance with Vietnamese law. Production retention/privacy and deployment remain blocked.
- Because the project foundation is uncommitted in the primary checkout, use Hermes `dir:<absolute project path>` sequentially instead of a worktree; a worktree would omit the existing untracked application files. Keep the task's file allowlist and preserve unrelated changes.

## Report format
Changed files; test commands/output/exit codes; TDD RED/GREEN evidence; acceptance trace; exact Hermes card/session; `NOT_VERIFIED` and `BLOCKED` items; no unsupported PASS claim.

## Definition of Done
- All in-scope acceptance criteria have evidence or are explicitly blocked/unverified.
- Independent Tester completes assigned checks without editing product code.
- Independent Security Reviewer concludes `APPROVED` or `CHANGES_REQUESTED` with severity-ranked findings.
- Ledger records actual Hermes routing/model/provider/profile/effort only when observed.
