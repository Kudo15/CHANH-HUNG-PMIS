# CHPMIS-012-F1 Final R2/R3 Independent Review

- **Task ID:** CHPMIS-012-F1-R2-R3-REV
- **Role:** Independent read-only Hermes Reviewer
- **Status:** COMPLETE — APPROVED (0 P1/P2/P3)
- **Harness / Card / Run:** Hermes CLI Kanban; card `t_f9a9870e`; run 114
- **Workspace:** `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`; existing dirty work and branch preserved
- **Requirement Trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; approved F1 task pack `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; R2 follow-up pack `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`; R3 cleanup pack `.team/tasks/CHPMIS-012-F1-R3-test-scope-cleanup.md`; accepted route design `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`; route plan `docs/superpowers/plans/2026-11-02-chpmis-012-f1-browser-bound-pkce.md`; `.team/ledger.md`
- **Worker Runs Audited:** Run 110 (`t_54dd05f6`), R2 run 112 (`t_85bc0983`), and R3 run 113 (`t_f518fc67`)

---

## 1. Scope Reviewed

Reviewed strictly within the approved F1/R2/R3 allowlist and boundaries:
- `backend/app/auth/oidc.py`
- Only the F1 `/login` and `/callback` cookie integration in `backend/app/auth/routes.py` (pre-existing role/authorization changes in `routes.py` were distinguished and preserved)
- `backend/app/auth/models.py`
- `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`
- F1/R2/R3 changes in `backend/tests/test_auth_oidc.py`
- F1 migration-head/preservation changes in `backend/tests/test_postgresql.py`
- `.team/tasks/CHPMIS-012-F1-worker-report.md`
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md` (including appended R3 sections 7 and 8)
- `.team/ledger.md` (historical record)

All pre-existing uncommitted modifications across unrelated files and other routes were preserved intact. No product code was changed or tests executed during this read-only review.

---

## 2. Independent Technical Audit & Line-by-Line Evidence

### 2.1 Conditional Atomic Delete and Affected-Row Handling (Race Protection)
- **Implementation:** In `backend/app/auth/oidc.py:354-361`, transaction consumption uses a direct database query delete:
  `affected = db.query(OIDCState).filter(OIDCState.state == state).delete(synchronize_session=False)`.
- **Rowcount Validation:** If `affected != 1`, it immediately rolls back (`db.rollback()`) and raises `HTTPException(status_code=400, detail="Invalid or missing state")` (`oidc.py:358-360`).
- **No Token Exchange on Losing Claim:** `client.exchange_code(...)` is strictly located at line 367, downstream of the successful atomic claim commit at line 361. If two callbacks loaded the same valid state concurrently, exactly one callback achieves `affected == 1`, commits, and reaches `exchange_code`. The second callback obtains `affected == 0`, rolls back, and fails closed with HTTP 400 before remote exchange.
- **Test Evidence:** `backend/tests/test_auth_oidc.py:792-879` (`test_callback_atomic_claim_prevents_stale_reader_double_exchange`) explicitly coordinates a stale-reader scenario using a custom session query hook. The losing transaction fails closed with HTTP 400 without raising an unhandled `StaleDataError` or invoking `mock_client.exchange_code`.

### 2.2 Transaction Retention on Missing / Mismatched Browser Binding
- **Pre-Consumption Validation:** In `backend/app/auth/oidc.py:343-348`:
  - If `browser_binding_cookie` is missing, `HTTPException(400, detail="Missing browser binding cookie")` is raised immediately.
  - If `hmac.compare_digest(stored_state.binding_digest, token_digest)` returns `False`, `HTTPException(400, detail="Invalid browser binding cookie")` is raised immediately.
- **Database Non-Deletion:** Neither check calls `db.delete(stored_state)` or modifies the database. Browser A's pending valid transaction remains intact.
- **Test Evidence:** Verified in `backend/tests/test_auth_oidc.py:529-589` and `643-669`, asserting `db.query(OIDCState).filter_by(state=state).first() is not None` following failed/mismatched cookie attempts, and confirming Browser A can subsequently redeem the state.

### 2.3 Callback Cookie Cleanup Coordination on Downstream Failures & Retention on Pre-Consumption Rejection
- **Service Notification Hook:** `process_callback` accepts an optional callback `on_consumed: Callable[[], None] | None = None` (`backend/app/auth/oidc.py:321`). `on_consumed()` is invoked at line 364 immediately after the atomic delete commit.
- **Route Coordination:** In `backend/app/auth/routes.py:71-119`:
  - `consumed` flag is tracked via a closure `mark_consumed()` passed to `process_callback`.
  - **Downstream HTTPException:** If `consumed` is `True`, lines 89-102 catch the exception, construct a `JSONResponse` preserving `exc.status_code`, `exc.detail`, and `exc.headers`, and clear `pmis_oidc_bind` via `response.delete_cookie(key=OIDC_BINDING_COOKIE_NAME, path="/", httponly=True, secure=settings.session_cookie_secure, samesite="lax")`.
  - **Downstream Unexpected Exception:** If `consumed` is `True`, lines 105-117 catch unexpected exceptions, return a safe `HTTP 500` JSONResponse `{"detail": "Authentication failed"}`, and clear the binding cookie.
  - **Pre-Consumption Failures:** If `consumed` is `False` (missing state, expired state, legacy state, missing binding cookie, mismatched binding cookie, or losing atomic claim), lines 103 and 118 execute `raise`, preserving the error without deleting the browser-binding cookie.
  - **Success Path:** Lines 134-140 clear `pmis_oidc_bind` upon successful authentication and session creation.
- **Test Evidence:** `backend/tests/test_auth_oidc.py:882-1022` (`test_callback_cookie_cleanup_on_downstream_failure_and_retention_on_pre_consumption_rejection`) verifies cookie deletion on downstream 502 (exchange failure) and 403 (inactive user), as well as cookie retention on pre-consumption 400 (mismatched cookie and unknown state).

### 2.4 PKCE S256, Verifier Secrecy, and Positive Token Request Body Assertion
- **Generation & Challenge:** `generate_code_verifier()` generates 32 bytes of entropy via `secrets.token_urlsafe(32)` (`backend/app/auth/oidc.py:23-24`). `generate_code_challenge()` computes the SHA-256 digest and base64url encoding without padding (`oidc.py:27-29`).
- **Secrecy:** `initiate_login_transaction` embeds `code_challenge` and `code_challenge_method="S256"` in authorization URL query parameters (`oidc.py:302-303`). `code_verifier` is stored only in `OIDCState.code_verifier` (`oidc.py:289`) and excluded from query parameters and logs (`backend/tests/test_auth_oidc.py:492, 516`).
- **Propagation:** `process_callback` passes `code_verifier` to `client.exchange_code(..., code_verifier=code_verifier)` (`oidc.py:367`).
- **Client Body Inclusion:** `DefaultOIDCClient.exchange_code` injects `data["code_verifier"] = code_verifier` into the form-urlencoded POST payload (`oidc.py:210-211`).
- **Positive Regression Test & R3 Scope:** `backend/tests/test_auth_oidc.py:1025-1069` (`test_default_oidc_client_token_request_body_carries_code_verifier`) verifies that `code_verifier` is present in the mocked token request form body. R3 run 113 removed the unrequested optional `code_verifier=None` omission subcase while preserving the positive assertion.

### 2.5 Fixed Callback URI
- **Fixed Source:** `effective_redirect_uri` is strictly sourced from `settings.oidc_redirect_uri` at initiation (`backend/app/auth/oidc.py:281, 286, 298`) and persisted in `OIDCState.redirect_uri`. During callback handling, `stored_state.redirect_uri` is passed to `exchange_code` (`oidc.py:351, 367`). No client-supplied redirect URI is accepted.

### 2.6 Constant-Time Binding Check & Digest Storage
- **Token Generation:** Browser token is 32 bytes of cryptographically secure random urlsafe text (`backend/app/auth/oidc.py:277`).
- **Digest Storage:** `hash_browser_token()` computes SHA-256 hex digest (`oidc.py:32-33`). Only `binding_digest` is persisted in `OIDCState` (`oidc.py:290`). Raw cookie token is never stored in DB.
- **Constant-Time Comparison:** Callback validation uses `hmac.compare_digest(stored_state.binding_digest, token_digest)` (`oidc.py:347`), preventing timing side-channel attacks.

### 2.7 Session and CSRF Preservation
- **Session/CSRF Attributes:** In `backend/app/auth/routes.py:142-160`:
  - Session cookie (`pmis_session`) is set with `httponly=True`, `secure=settings.session_cookie_secure`, `samesite=settings.session_cookie_samesite`, `path="/"`.
  - CSRF cookie (`pmis_csrf`) is set with `httponly=False`, `secure=settings.session_cookie_secure`, `samesite=settings.session_cookie_samesite`, `path="/"`.
  - Attributes and session validation in `/session` remain fully preserved (`routes.py:163-180`).

### 2.8 Additive Nullable Migration and Data Preservation
- **Migration `0007_oidc_pkce_browser_binding.py`:**
  - Adds `code_verifier` (`String(128)`, `nullable=True`) and `binding_digest` (`String(64)`, `nullable=True`) to `oidc_states` via `op.batch_alter_table` (`lines 20-24`).
  - Implements clean symmetrical downgrade dropping both columns (`lines 26-29`).
- **Contract & Preservation Tests:** In `backend/tests/test_postgresql.py`:
  - `EXPECTED_REVISION = "0007_oidc_pkce_browser_binding"` (`line 23`).
  - Columns asserted in `oidc_states` schema inspector (`lines 175-186`).
  - `test_postgresql_upgrade_from_0006_preserves_oidc_state_rows_and_nullable_pkce_fields` (`lines 350-405`) verifies that synthetic rows created under revision 0006 are preserved across the upgrade to 0007 with `NULL` values in new columns.

---

## 3. Findings

- **P1 (Critical / Security Blocker):** None.
- **P2 (Major / Specification Deviation):** None.
- **P3 (Minor / Quality / Edge Case):** None.

---

## 4. Declined to Judge / External Verification Limits

1. **Live IdP (Keycloak) and Browser E2E:** Live end-to-end authentication with Keycloak and automated browser sessions is intentionally out of scope for F1 and tracked under downstream CHPMIS-012 milestones.
2. **Live PostgreSQL Runtime:** Live PostgreSQL test runs (`backend/tests/test_postgresql.py`) remain skipped (`NOT_VERIFIED`) due to `TEST_DATABASE_URL` being unset in the local environment, as truthfully reported by the Worker.
3. **OpenCode Verifier:** OpenCode read-only verifier execution remains pending external provider availability / authorization and is not judged here.

---

## 5. Review Verdict

**APPROVED**

The final scoped diff across Worker run 110, R2 run 112, and R3 run 113 satisfies all requirements:
1. Concurrency protection via conditional atomic database delete and affected-row verification before token exchange.
2. Complete cookie cleanup coordination across all downstream error paths and successful authentication, with strict retention on pre-consumption rejections.
3. Browser A transaction preservation against unauthorized swapping or missing binding.
4. Cryptographic S256 PKCE with verifier secrecy in authorization URLs and verified form-body propagation.
5. Symmetrical additive nullable Alembic migration preserving existing 0006 data.
6. Preservation of all pre-existing uncommitted work and adherence to file allowlists.
