# Task Pack — CHPMIS-003-F1 Authentication Security Remediation

## Task ID and execution role
- Task ID: CHPMIS-003-F1
- Role: Hermes Worker + independent Tester + independent Security Reviewer
- Status: COMPLETE — independent Tester PASS and Security Reviewer APPROVED; owner-approved HG1/HG2 remain in force.

## Context and objective
The CHPMIS-003 Worker implemented the OIDC/session/authorization foundation and an independent Tester reported 31 passed/1 skipped, Ruff clean, and offline Alembic validation success. Independent Security Reviewer card `t_044adca0` returned `CHANGES_REQUESTED` with 2 P1, 1 P2, and 1 P3 findings. Fix only these findings, test each fix, and retain all unrelated working-tree state. No code may be modified by the Coordinator/Tester/Reviewer.

The security review findings were verified against current code:
1. `backend/app/auth/oidc.py:41-46`: `decode_and_verify_id_token()` only base64-decodes claims; the signature is never checked.
2. `backend/app/auth/routes.py:31-34` and the grant/revoke routes: caller supplies `second_admin_id` in JSON; code loads that admin and treats their existence/role as approval, without that second admin authenticating or acting.
3. `backend/app/auth/oidc.py:86-108`: `initiate_login()` accepts an arbitrary `redirect_uri` parameter and persists it, though current `/login` route does not expose it.
4. `backend/app/auth/oidc.py:96-108`: expired OIDC state rows are not pruned on new login; only the matching state is deleted on callback.

## Approved decisions and references
- Follow `OPEN_QUESTIONS.md`, `docs/security/SECURITY_MODEL.md`, and CHPMIS-003 task pack. OIDC claims are accepted only after cryptographic signature, issuer, audience, expiry, and nonce verification; session policy remains Secure=true, SameSite=Lax, 30-minute idle, 12-hour absolute.
- The actual organization IdP is not selected. Use deterministic local keys/mocks in tests; make no real IdP network request. Actual provider connectivity remains `NOT_VERIFIED`.
- The second-admin rule is a two-person action: the approver identity must come from a separate authenticated session/principal, never a request-body identity. Keep grant/revocation state durable for audit; do not silently erase approved request history.
- Redirect URI must be the fixed configured callback URI; never accept a callback/redirect target supplied by the browser/request body.
- Remove stale OIDC state rows at or before expiration during login initiation (or another bounded, tested cleanup point); never affect unexpired state.
- Official PyJWT API docs state `jwt.decode` verifies the cryptographic signature and warn to hard-code/configure the algorithm allowlist, not derive it from token input: https://pyjwt.readthedocs.io/en/stable/api.html . PyJWT documents JWKS key resolution through `PyJWKClient`: https://pyjwt.readthedocs.io/en/latest/usage.html . The retrieved current official docs identify PyJWT 2.15.1; if using PyJWT, pin `PyJWT[crypto]==2.15.1` consistently in project requirements/constraints. Do not implement JWT cryptography manually.

## Objective
Close the four Security Reviewer findings with minimum additive changes and regression tests. The ID-token verifier must use a maintained JOSE/JWT library, an injected/configured trusted signing-key resolver, and a fixed algorithm allowlist; no decoded-but-unverified claims may reach user/session creation.

For System Admin role changes, replace the one-request “second_admin_id” assertion with a durable two-step request/approval flow. One authenticated System Admin requests grant/revocation; a different authenticated System Admin separately approves. The approval endpoint obtains actor identity only from the validated session. Keep the approved/revoked request record as durable history. Do not implement initial-admin bootstrap.

## Files in scope
- Modify: `backend/app/auth/oidc.py`, `backend/app/auth/routes.py`, `backend/app/auth/models.py`, `backend/app/config.py` only as needed for trusted JWKS/config boundary.
- Create one additive migration under `backend/alembic/versions/**` only if the two-step role-change request requires durable storage.
- Modify/create: `backend/tests/test_auth_oidc.py`, `backend/tests/test_auth_policy.py`, and/or a focused auth-route test under `backend/tests/**`.
- Modify `backend/requirements.txt`, `backend/constraints.txt`, or `.env.example` only if the verified signing library/JWKS setting requires it; placeholders only.
- Forbidden: `ACCEPTANCE.md`, ledger/plan/task register, project/task schema or endpoints, generic audit/dashboard implementation, frontend, Compose/CI, docs outside this task, real identities/secrets, real IdP calls, production/deployment, unrelated cleanup.

## Acceptance criteria
- [ ] ID tokens are signature-verified with a maintained library and key resolved from a trusted configured JWKS source/provider boundary. The algorithm allowlist is fixed/configured and cannot be selected from the token's untrusted `alg` header. Tests use an ephemeral local signing key/resolver and perform no network calls.
- [ ] Valid signature, `iss`, `aud`, `exp`, `sub`, nonce, and relevant OIDC claims are required/validated. Invalid signature, unknown `kid`, unsupported algorithm, malformed token, wrong issuer/audience, expired token, missing required claim, and wrong nonce fail closed before user/session writes.
- [ ] Remove test-only unsigned JWT token generation from production auth code; build signed test tokens in test helpers.
- [ ] Grant/revoke begins as a durable pending request; no privilege changes until a second authenticated System Admin approves through a separate action. Approver is obtained from the session principal, not a client-supplied ID; same requester/approver and self-grant are rejected. An approval request cannot be replayed to apply twice.
- [ ] Approved System Admin grant/revocation request history remains durable with requester, approver, target, action, request time, and approval time/status; no automatic retention purge is added.
- [ ] OIDC login always uses the configured callback URI. No untrusted request parameter can replace it. Tests cover attempted redirect manipulation.
- [ ] Expired OIDC states are removed at a bounded cleanup point while unexpired state remains available; tests verify the boundary.
- [ ] All additive migrations are reversible and do not create project/task tables.
- [ ] Worker reports TDD RED/GREEN and exact tests/lint/offline migration commands/exit codes; actual IdP and PostgreSQL runtime remain `NOT_VERIFIED` if unavailable.

## Verification commands and evidence
- Backend tests: run the repository's working Windows venv command (Tester observed `.venv/Scripts/python -m pytest -v` from `backend/`) and record the exact exit code/output.
- Lint: Tester observed `.venv/Scripts/ruff.exe check .` from `backend/`; record exact result.
- Alembic: offline `upgrade head --sql` and downgrade SQL generation from the new revision to its predecessor; record exact commands and exit codes.
- Tester independently reruns these commands; Security Reviewer checks each finding and the diff read-only.
- No test command may call a real IdP or depend on Docker/PostgreSQL availability.

## Prompt template
- Library: prompts.chat via `.agents/skills/prompt-lookup`.
- Template: **Feature coding template**, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Full template retrieved on 2026-10-30 and reused because this is a bounded implementation follow-up to CHPMIS-003. Modernized worker prompt: “Implement only CHPMIS-003-F1 from the supplied task pack. Verify all four findings against code before changing it. Use TDD: add signed-token/forged-signature, authenticated two-person approval, fixed-redirect, and stale-state cleanup tests; show RED; make the smallest safe changes; show GREEN. Use a vetted JOSE library and a fixed algorithm allowlist; do not implement signature crypto manually or call a real IdP. Use separate authenticated requester and approver actions; never trust approver identity from request JSON. Preserve Secure/SameSite/timeouts and all unrelated dirty state. Do not edit acceptance, ledger, plan, frontend, CI, Compose, or project/task schema. Report file list, commands/output/exit codes, migration evidence, and remaining NOT_VERIFIED items; request independent review and do not self-approve.”

## Risks and boundaries
- The authentication schema change is additive and within approved HG1/HG2. Do not rewrite/drop existing auth tables or seed users/roles.
- Actual provider/JWKS connectivity remains unverified until a specific IdP is separately approved/configured; no real network calls are authorized in this local task.
- Initial System Admin bootstrap stays open in `OPEN_QUESTIONS.md`; tests may create synthetic admins only.
- No Vietnamese legal-compliance claim; this task does not approve production.
- Existing project foundation and CHPMIS-003 files are uncommitted/untracked in the current checkout. Work sequentially in the existing `dir:` workspace; do not clean/reset. The independent Reviewer gets a separate read-only Hermes card/session after Tester.

## Definition of Done
- Worker closes all four findings within scope with evidence or explicitly blocks any infeasible item.
- Independent Tester reports exact evidence without implementation edits.
- Independent Security Reviewer returns `APPROVED` or `CHANGES_REQUESTED` with file/line priorities.
- Ledger records actual Hermes card/session/profile/model/provider/effort only when observed.
