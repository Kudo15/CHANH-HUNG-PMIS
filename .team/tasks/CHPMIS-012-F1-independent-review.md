# CHPMIS-012-F1 Independent Review

- **Task ID:** CHPMIS-012-F1-R1
- **Role:** Independent read-only Hermes Reviewer
- **Status:** COMPLETE — APPROVED (0 P1/P2/P3)
- **Harness / Card / Run:** Hermes CLI Kanban; card `t_bba958db`; run 111
- **Workspace:** `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`; existing dirty work and branch preserved
- **Requirement Trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`; `docs/superpowers/plans/2026-11-02-chpmis-012-f1-browser-bound-pkce.md`
- **Worker Run Under Review:** `t_54dd05f6` / run 110 (`.team/tasks/CHPMIS-012-F1-worker-report.md`)

---

## 1. Scope Reviewed

Reviewed strictly within the approved F1 allowlist:
- `backend/app/auth/oidc.py`
- `backend/app/auth/routes.py` (strictly the F1 `/login` and `/callback` cookie glue)
- `backend/app/auth/models.py`
- `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`
- `backend/tests/test_auth_oidc.py`
- `backend/tests/test_postgresql.py` (migration-head update and synthetic row preservation test)
- `.team/tasks/CHPMIS-012-F1-worker-report.md`

All pre-existing uncommitted modifications in `backend/app/auth/routes.py`, `backend/tests/test_postgresql.py`, and `0006_bootstrap_trust_boundary.py` were distinguished and preserved. No product code was altered during this review.

---

## 2. Requirement Verification & Line-by-Line Evidence

### 2.1 Browser-Bound S256 PKCE and Verifier Secrecy
- **Generation:** `generate_code_verifier()` generates 32 bytes of cryptographic randomness via `secrets.token_urlsafe(32)` (`backend/app/auth/oidc.py:23-24`).
- **Challenge:** `generate_code_challenge()` computes SHA-256 over ASCII verifier and outputs base64url-encoded string without padding (`backend/app/auth/oidc.py:27-29`).
- **Secrecy:** `initiate_login_transaction` includes `code_challenge` and `code_challenge_method="S256"` in authorization URL query parameters (`backend/app/auth/oidc.py:302-303`), while `code_verifier` is stored server-side in `OIDCState.code_verifier` (`backend/app/auth/oidc.py:289`) and never exposed in the authorization URL (`backend/tests/test_auth_oidc.py:483, 507`).

### 2.2 Random Binding Token Storage-by-Digest & Constant-Time Comparison
- **Browser Token:** `browser_token = secrets.token_urlsafe(32)` generated at initiation (`backend/app/auth/oidc.py:277`).
- **Digest Storage:** `hash_browser_token()` computes SHA-256 hex digest (`backend/app/auth/oidc.py:32-33`). `binding_digest` is persisted in `OIDCState.binding_digest` (`backend/app/auth/oidc.py:290`). Raw cookie token is never stored in DB or logs (`backend/tests/test_auth_oidc.py:508-510`).
- **Constant-Time Match:** In `process_callback`, verification uses `hmac.compare_digest(stored_state.binding_digest, token_digest)` (`backend/app/auth/oidc.py:346-347`).

### 2.3 Non-Consumption on Swapping / Binding Failure
- When `browser_binding_cookie` is missing (`backend/app/auth/oidc.py:342-343`) or digest comparison fails (`backend/app/auth/oidc.py:346-347`), an `HTTPException(400)` is raised without deleting `stored_state`.
- Legitimate Browser A transaction is preserved intact when Browser B attempts unauthorized redemption (`backend/tests/test_auth_oidc.py:643-660`).

### 2.4 Atomic One-Time Consumption and Replay Prevention
- Upon valid browser-binding match, `stored_state` is deleted and committed immediately before code exchange (`backend/app/auth/oidc.py:354-355`).
- Any subsequent callback replay fails closed with 400 (`backend/app/auth/oidc.py:326-327`; regression at `backend/tests/test_auth_oidc.py:698-702, 774-778`).

### 2.5 Verifier Propagation to Token Exchange
- `OIDCClient` protocol and implementations accept optional `code_verifier: str | None = None` (`backend/app/auth/oidc.py:157, 178, 196`).
- `process_callback` propagates `code_verifier=code_verifier` to `client.exchange_code(...)` (`backend/app/auth/oidc.py:358`).
- `DefaultOIDCClient.exchange_code` includes `code_verifier` in the POST body to the token endpoint (`backend/app/auth/oidc.py:210-211`).

### 2.6 Fixed Callback URI
- `effective_redirect_uri` is strictly sourced from `settings.oidc_redirect_uri` (`backend/app/auth/oidc.py:281, 286, 298, 350`). No client-supplied redirect URI is accepted.

### 2.7 Fail-Closed Legacy and Expired Transactions
- Expired state is deleted and rejected with 400 (`backend/app/auth/oidc.py:330-333`).
- Legacy rows missing `code_verifier` or `binding_digest` are deleted and rejected with 400 (`backend/app/auth/oidc.py:336-339`; regression at `backend/tests/test_auth_oidc.py:583-611`).

### 2.8 Route Cookie Integration & Session/CSRF Preservation
- In `backend/app/auth/routes.py`:
  - `/login` sets `pmis_oidc_bind` cookie with `HttpOnly=True`, `Secure=settings.session_cookie_secure`, `SameSite=lax`, `Path="/"`, `max_age=600` (`lines 47-55`).
  - `/callback` retrieves `request.cookies.get(OIDC_BINDING_COOKIE_NAME)` and passes it to `process_callback` (`lines 69, 75`).
  - Upon successful transaction, `/callback` clears `pmis_oidc_bind` via `response.delete_cookie(key=OIDC_BINDING_COOKIE_NAME, path="/", httponly=True, secure=settings.session_cookie_secure, samesite="lax")` (`lines 94-100`).
  - Existing session cookie (`pmis_session`) and CSRF cookie (`pmis_csrf`) configuration and attributes are strictly preserved (`lines 103-119`).

### 2.9 Additive Nullable Migration and Data Preservation
- Migration `0007_oidc_pkce_browser_binding` revises `0006_bootstrap_trust_boundary` and adds nullable `code_verifier` (String(128)) and `binding_digest` (String(64)) columns to `oidc_states` using batch operations (`backend/alembic/versions/0007_oidc_pkce_browser_binding.py:20-29`).
- `backend/tests/test_postgresql.py`:
  - `EXPECTED_REVISION` advanced to `0007_oidc_pkce_browser_binding` (`line 23`).
  - `test_postgresql_upgrade_from_0006_preserves_oidc_state_rows_and_nullable_pkce_fields` inserts synthetic 0006 state row, upgrades to 0007 head, and verifies row is preserved with NULL in new fields (`lines 345-405`).

---

## 3. Findings

- **P1 (Critical / Security Blocker):** None.
- **P2 (Major / Specification Deviation):** None.
- **P3 (Minor / Quality / Edge Case):** None.

---

## 4. Declined to Judge / External Verification Limits

- **Live IdP (Keycloak) and Browser E2E:** Live end-to-end authentication with Keycloak and automated browser sessions is intentionally out of scope for F1 and tracked under downstream CHPMIS-012 milestones.
- **Live PostgreSQL Runtime:** Live PostgreSQL test runs (`backend/tests/test_postgresql.py`) remain skipped (`NOT_VERIFIED`) due to `TEST_DATABASE_URL` being unset in the local environment, as truthfully reported by the Worker.

---

## 5. Review Verdict

**APPROVED**

The implementation satisfies all criteria specified in `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`, conforms to the approved design and plan, maintains strict separation of concerns, enforces browser-bound S256 PKCE without verifier leakage, protects against callback swapping and replay, preserves pre-existing schema and uncommitted work, and provides comprehensive unit/integration regression coverage.
