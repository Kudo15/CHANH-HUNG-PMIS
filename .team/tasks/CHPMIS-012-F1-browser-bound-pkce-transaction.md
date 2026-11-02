# CHPMIS-012-F1 — Browser-bound OIDC transaction and PKCE

- **Task ID:** CHPMIS-012-F1
- **Role:** Hermes Worker (sole product-code writer), then OpenCode read-only Tester and separate Hermes Reviewer.
- **Status:** IN REVIEW / VERIFICATION BLOCKED — F1 Worker run 110 completed the approved implementation. R1 Reviewer run 111 approved with 0 findings, then Coordinator follow-up found an atomic-consumption race and missing cookie cleanup after consumed-transaction errors; R2 run 112 implemented those fixes and R3 run 113 removed an out-of-scope omission test. Focused tests, full backend suite, Ruff check/format, and root diff check have passing Worker evidence. Live PostgreSQL remains `NOT_VERIFIED` because the owner confirmed `TEST_DATABASE_URL` was unset in run 107's shell; no value was shared. The fresh independent review of the final R2/R3 diff approved with 0 findings (Reviewer card `t_f9a9870e`, run 114; `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md`). The owner-approved OpenCode verifier run `2026-11-02T02-53-03-verifier-chpmis-012-f1-final-read-only-verificati-467b` read the approved task/evidence files, but its role-level shell permission denied all seven checks before execution; each is `NOT_VERIFIED`, with no command exit code. No verifier settings or permissions were changed. Runs 107–109 remain historically blocked for their process deviations. Design and plan: `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`, `docs/superpowers/plans/2026-11-02-chpmis-012-f1-browser-bound-pkce.md`.
- **Trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; current OIDC implementation in `backend/app/auth/oidc.py`, `backend/app/auth/models.py`, `backend/app/auth/routes.py`; current schema head `0006_bootstrap_trust_boundary`.
- **Prompt template:** Real prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, located/retrieved through `.agents/skills/prompt-lookup` and recorded in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`. Modernized for this task: inspect the existing auth flow and migration head; use test-first RED/GREEN; implement only the enumerated browser-bound OIDC transaction requirements; preserve existing token/session controls; run only the commands below; report exact paths, commands, exit codes and remaining verification limits. No commit/stage/push/deploy, host changes, provider permission changes, real identity, secret output, or scope expansion.
- **Branch/baseline:** Existing dirty branch `audit-remediation/verify-audit-findings`; baseline SHA `7a27930bd3f80d4d08bcf9ed55ae829c90ca7637`; current workspace contains pre-existing uncommitted changes. Preserve all; do not clean/reset/stash. Work in the assigned current repository workspace and only this allowlist.

## Objective

Harden the existing authorization-code flow against login CSRF/code interception and callback transaction swapping. Each initiated login must use an S256 PKCE challenge, a cryptographically random verifier, a short-lived browser binding cookie, strict state/nonce/issuer/audience validation, exact configured callback URI, and one-time transaction consumption. A callback replayed in a different browser must fail before token exchange or session creation. Keep local/browser cookies `Secure`, `HttpOnly` where applicable, and `SameSite=Lax`; do not relax CSRF or token verification.

This task does not implement the complete CHPMIS-012 frontend/Keycloak/PostgreSQL E2E. It makes no claim about a live IdP or browser until later CHPMIS-012 tasks run.

## Allowed files

Modify only:

- `backend/app/auth/oidc.py`
- `backend/app/auth/routes.py` only for explicit HTTP cookie integration: set the short-lived browser-binding cookie on the `/login` redirect response, pass the cookie value from the callback request into OIDC transaction validation, and clear it when the transaction is consumed. Do not change other routes, responses, authorization or session policy.
- `backend/app/auth/models.py`
- `backend/app/config.py` only if a new OIDC browser-cookie setting is strictly required; defaults must preserve secure policy
- One additive Alembic migration after `0006_bootstrap_trust_boundary.py`
- `backend/tests/test_auth_oidc.py`
- `backend/tests/test_postgresql.py` only to advance the migration-head/schema contract and test preservation of pre-existing OIDC state rows
- Append-only `.team/tasks/CHPMIS-012-F1-worker-report.md`

Do not alter frontend, Compose, Keycloak realm, environment files, dependencies, old migrations, roles, authorization policy, session/CSRF semantics, bootstrap, business workflows, or unrelated dirty files. In `backend/app/auth/routes.py`, limit changes strictly to the approved cookie set/pass/clear integration described above. If any other file or behavior is needed, stop and request a scoped update.

## Required behavior and TDD

1. Add focused failing tests before implementation for: PKCE `code_challenge_method=S256`; challenge/verifier match; verifier is random and never included in the authorization URL; secure browser-binding cookie is set; callback without/mismatched browser binding is rejected before code exchange; a different TestClient/browser cannot redeem browser A's state; matching browser can complete the existing signed-token validation; expired state, replay and invalid callback URI fail closed and do not create a session; state/cookie are one-time consumed; existing CSRF/session cookie flags and issuer/audience/nonce checks remain intact.
2. Observe RED for the intended missing behavior before editing implementation.
3. Add only the minimal nullable migration columns needed to preserve pre-existing ephemeral `oidc_states` rows; new flows must always populate verifier and browser-binding digest, and callbacks without them must fail closed. Do not store raw browser binding tokens. Write a migration test from 0006 with synthetic state data and assert the row is preserved while new columns are nullable for compatibility.
4. Use PKCE S256 and constant-time comparison for browser-binding digests. Consume the transaction atomically/one time before remote token exchange, as current code does. Never log authorization codes, verifier, binding cookie, token response, or secrets. Bind exact configured redirect URI; do not accept a callback URL from request input.
5. Keep the existing OIDC signature, issuer, audience, nonce, expiry, active-user, session, secure-cookie, SameSite and CSRF contracts.
6. Keep HTTP cookie operations explicit at the route boundary: set the binding cookie on the login redirect using Secure/HttpOnly/SameSite=Lax attributes, pass its value from the callback request to the OIDC service, and clear it after the transaction is consumed. Do not use implicit request-context access, frame inspection, monkey-patching, or middleware outside this allowlist.

## Verification commands

Use only existing repository commands. From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` with `TEST_DATABASE_URL` configured to the existing isolated synthetic PostgreSQL test service; if unavailable, record exact skip/NOT_VERIFIED, never PASS.
3. `.venv\Scripts\python.exe -m pytest -q`
4. `.venv\Scripts\ruff.exe check . ../dev`
5. `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`
6. `.venv\Scripts\python.exe -m alembic upgrade head --sql`

From repository root:

7. `git diff --check`

Do not start Docker/Keycloak or connect to external providers in this task. Report exact command, working directory, output summary and exit code; distinguish skips from passing live PostgreSQL checks.

## Definition of Done

- RED then GREEN evidence is present in the append-only Worker report.
- Only the allowlist changed; all requirements above have focused regressions.
- All listed source checks are reported truthfully; live PostgreSQL evidence is required if the configured synthetic service is available.
- Worker requests review and does not declare the CHPMIS-012/platform gate complete.
- OpenCode Tester independently runs assigned read-only checks when its configured provider is available; any permission/provider failure is `NOT_VERIFIED` without changing settings.
- Independent Hermes Reviewer reads full scoped diff and task evidence, then returns `APPROVED` or `CHANGES_REQUESTED` with P1–P3 findings.
- No commit, stage, push, deploy, secrets, real agency identities, host provisioning, or unrelated edits.
