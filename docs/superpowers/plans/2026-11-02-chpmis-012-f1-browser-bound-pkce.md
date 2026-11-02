# CHPMIS-012-F1 Browser-Bound OIDC and PKCE Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Bind every OIDC authorization-code transaction to one browser, require S256 PKCE, and reject expired, replayed, swapped, or invalid callbacks before token exchange or session creation.

**Architecture:** Keep transaction creation, PKCE, digest validation, and one-time state consumption in the OIDC service. Add only explicit HTTP cookie set/pass/clear glue at the existing auth routes. Add nullable migration columns so existing ephemeral state rows survive the schema upgrade while legacy rows fail closed at callback time.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Alembic, pytest, PostgreSQL, stdlib `secrets`, `hashlib`, `base64`, and `hmac`.

**Spec:** `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; route boundary decision: `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`.

## Global Constraints

- Modify only the F1 task pack allowlist, including `backend/app/auth/routes.py` only for binding-cookie set/pass/clear glue.
- Use S256 PKCE, cryptographically random verifier and browser token, constant-time digest comparison, and one-time state consumption before remote exchange.
- The browser cookie is Secure, HttpOnly, SameSite=Lax, short-lived, and path `/`; store only its digest, never the raw token.
- Keep callback URI fixed to `settings.oidc_redirect_uri`; preserve signature, issuer, audience, nonce, expiry, active-user, session, CSRF, and cookie checks.
- Add one additive migration after `0006_bootstrap_trust_boundary`; new verifier and digest columns are nullable only for old-row compatibility, and callbacks reject rows missing either value.
- Keep existing two-argument `DefaultOIDCClient.exchange_code(code, redirect_uri)` callers working; production callback flow must pass the verified verifier to token exchange.
- Do not change frontend, Compose, Keycloak, dependencies, authorization policy, session/CSRF semantics, bootstrap, or unrelated dirty files. Do not commit, stage, push, deploy, start services, or contact external providers.

## Review Focus

1. Missing or mismatched browser cookie must fail before token exchange; tests assert the exchange client was not called.
2. A row created before the new columns existed must be preserved by migration and then rejected at callback time; test the migration and legacy-row path.
3. Expired and replayed state must not exchange twice or create a session; pin expiry and one-time behavior in focused route/service tests.
4. A request-supplied redirect URI must never replace the configured callback URI; retain and extend the fixed-URI regression.
5. Verifier and cookie handling must not leak secrets: assert the authorization URL contains a challenge but no verifier, the cookie attributes are exact, and only a digest is stored.

---

### Task 1: Browser-bound OIDC transaction and callback

**Files:**
- Modify: `backend/app/auth/oidc.py`
- Modify: `backend/app/auth/routes.py` — only `/login` binding-cookie set, `/callback` cookie pass, and consumed-transaction cookie clear.
- Modify: `backend/app/auth/models.py`
- Modify: `backend/app/config.py` only if a new cookie setting is strictly required; prefer a fixed module constant and make no config edit otherwise.
- Create: one Alembic migration after `backend/alembic/versions/0006_bootstrap_trust_boundary.py`.
- Modify: `backend/tests/test_auth_oidc.py`
- Modify: `backend/tests/test_postgresql.py` only for migration-head/schema and synthetic old-state preservation coverage.
- Append: `.team/tasks/CHPMIS-012-F1-worker-report.md`

**Interfaces:**
- Add `initiate_login_transaction(db: DBSession, settings: Settings) -> tuple[str, str]`, returning `(authorization_url, raw_browser_binding_cookie)` for the HTTP route. Keep the existing `initiate_login(db, settings) -> str` string contract used by `test_auth_remediation.py` outside this allowlist.
- Extend `process_callback` with an explicit `browser_binding_cookie: str | None` input. The route passes `request.cookies.get(<binding-cookie-name>)`; service code does not inspect request context.
- Extend `OIDCClient.exchange_code` with an optional `code_verifier: str | None = None` parameter so existing two-argument test callers continue to work. The validated callback path always supplies its stored verifier to `DefaultOIDCClient`.
- Add nullable `OIDCState` fields for the code verifier and browser-binding digest. The cookie name must be a fixed local constant unless the implementation demonstrates that configuration is required.

- [ ] **Step 1: Add focused failing service tests.** Extend or add tests covering S256 challenge/verifier correspondence, verifier absence from the authorization URL, browser-token randomness/digest-only storage, missing and mismatched cookie rejection before exchange, legacy rows failing closed, fixed redirect URI, expiry, replay, and existing signed-token claim checks.
- [ ] **Step 2: Run the focused tests and record RED.** Run from `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`. Record the exact failing assertions and exit code before implementation.
- [ ] **Step 3: Add focused route and migration regressions and observe RED.** In `test_auth_oidc.py`, assert `/login` sets a Secure/HttpOnly/SameSite=Lax/root-path short-lived cookie; same-browser callback succeeds; a different TestClient/browser and callback replay fail before exchange; consumed callbacks clear the binding cookie while preserving existing session and CSRF cookie flags and response status/details. In `test_postgresql.py`, add `test_postgresql_upgrade_from_0006_preserves_oidc_state_rows_and_nullable_pkce_fields`: seed a synthetic `oidc_states` row at revision `0006_bootstrap_trust_boundary`, upgrade to head, and assert the row remains with nullable new fields. Run each relevant test before implementation; if the isolated PostgreSQL service is unavailable, record migration RED/GREEN as NOT_VERIFIED.
- [ ] **Step 4: Implement the smallest service, migration, and route change.** Generate S256 PKCE and a random browser binding; persist the verifier and only the binding digest; validate expiry, state, browser digest, and callback URI; consume once before token exchange; send the verifier in the token request; set/pass/clear the cookie only at the route boundary. Add only nullable columns and update current-head assertions without rewriting old revisions. Do not use implicit request-context access, frame inspection, monkey-patching, or middleware.
- [ ] **Step 5: Run the exact focused and full verification commands.** From `backend/`, run `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`; `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` with the existing isolated synthetic PostgreSQL service (otherwise record the exact skip/NOT_VERIFIED); `.venv\Scripts\python.exe -m pytest -q`; `.venv\Scripts\ruff.exe check . ..\dev`; `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`; and `.venv\Scripts\python.exe -m alembic upgrade head --sql`. From repository root, run `git diff --check`. Record each command, working directory, output summary, and exit code.
- [ ] **Step 6: Append the Worker report and request independent review.** Include RED/GREEN evidence, changed files, exact checks, requirement trace, deviations, and all NOT_VERIFIED limits. Do not claim live IdP/browser E2E or close CHPMIS-012.

**Worker method:** The repository routing instruction requires a fresh Hermes Worker card; use the approved prompt template already cited in the task pack and the exact-card launch process. Do not resume the first blocked card.

**Review gate:** After Worker evidence, use the separately authorized read-only Tester only if its task payload/destination is approved, then obtain an independent Hermes Reviewer verdict against the full scoped diff. No task completion claim before review.
