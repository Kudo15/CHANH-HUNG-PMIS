# CHPMIS-012-F1 Worker Implementation Report

- **Task ID:** CHPMIS-012-F1
- **Role:** Hermes Worker (implementation)
- **Status:** READY_FOR_REVIEW
- **Trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; `docs/superpowers/plans/2026-11-02-chpmis-012-f1-browser-bound-pkce.md`; `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`
- **Prompt Template:** Real prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`

---

## 1. Scope and Allowed Files

Modified strictly within the approved F1 allowlist:
- `backend/app/auth/oidc.py`: PKCE S256 helper generation, `pmis_oidc_bind` cookie constant, SHA-256 digest hashing of browser tokens, `initiate_login_transaction` returning `(auth_url, browser_token)` while preserving `initiate_login -> str` signature, explicit `browser_binding_cookie` parameter in `process_callback`, non-destructive binding verification before atomic consumption, verifier propagation to `DefaultOIDCClient.exchange_code`.
- `backend/app/auth/routes.py`: Explicit HTTP cookie integration at `/login` (sets `pmis_oidc_bind` with `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, `Max-Age=600`) and `/callback` (extracts `pmis_oidc_bind`, passes to OIDC service, and clears cookie via `delete_cookie(..., httponly=True, secure=..., samesite='lax')` upon consumption).
- `backend/app/auth/models.py`: Added nullable `code_verifier` (String(128)) and `binding_digest` (String(64)) columns to `OIDCState`.
- `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`: Additive migration adding nullable `code_verifier` and `binding_digest` columns to `oidc_states`, revising head from `0006_bootstrap_trust_boundary`.
- `backend/tests/test_auth_oidc.py`: Unit and integration regressions for PKCE S256 challenge/verifier correspondence, absence of verifier from authorization URL, browser token digest storage, missing/mismatched cookie rejection before exchange, non-consumption of valid transaction on foreign browser swap attempts, legacy row fail-closed behavior, and cookie clearing on completion.
- `backend/tests/test_postgresql.py`: Updated `EXPECTED_REVISION = "0007_oidc_pkce_browser_binding"` and added migration test asserting synthetic `oidc_states` row at revision 0006 is preserved with nullable new columns upon upgrade to 0007.
- `.team/tasks/CHPMIS-012-F1-worker-report.md`: Worker report artifact.

Pre-existing changes across unrelated files were strictly preserved. No other files were created or modified.

---

## 2. TDD RED Evidence

Focused test regression added to `backend/tests/test_auth_oidc.py` (`test_callback_browser_swapping_rejected_and_different_client_cannot_redeem` and `test_callback_rejects_missing_or_mismatched_browser_binding`) asserting that a missing or mismatched browser cookie fails closed before code exchange without consuming another browser's pending valid transaction.

- **Command:** `'.venv\Scripts\python.exe' -m pytest -q tests/test_auth_oidc.py`
- **Working Directory:** `backend/`
- **Exit Code:** `1`
- **Output:**
```
.........F.F.                                                            [100%]
================================== FAILURES ===================================
_________ test_callback_rejects_missing_or_mismatched_browser_binding _________
...
tests\test_auth_oidc.py:552: AssertionError: assert None is not None
_ test_callback_browser_swapping_rejected_and_different_client_cannot_redeem __
...
tests\test_auth_oidc.py:645: AssertionError: assert None is not None
FAILED tests/test_auth_oidc.py::test_callback_rejects_missing_or_mismatched_browser_binding
FAILED tests/test_auth_oidc.py::test_callback_browser_swapping_rejected_and_different_client_cannot_redeem
2 failed, 11 passed, 1 warning in 17.07s
```

---

## 3. TDD GREEN Evidence

Implementation in `backend/app/auth/oidc.py` corrected to validate browser binding without deleting `stored_state` on missing/invalid cookie. State deletion occurs atomically only upon valid binding verification before code exchange.

- **Command:** `'.venv\Scripts\python.exe' -m pytest -q tests/test_auth_oidc.py`
- **Working Directory:** `backend/`
- **Exit Code:** `0`
- **Output:**
```
.............                                                            [100%]
13 passed, 1 warning in 2.59s
```

---

## 4. Verification Commands & Results

All 7 required verification commands from the task specification were run without deviations:

### 1. Focused OIDC Tests
- **Command:** `'.venv\Scripts\python.exe' -m pytest -q tests/test_auth_oidc.py`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Output:** `13 passed, 1 warning in 2.59s`

### 2. PostgreSQL Test Suite
- **Command:** `'.venv\Scripts\python.exe' -m pytest -q tests/test_postgresql.py`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Output:** `6 skipped, 1 warning in 1.42s`
- **Status:** `NOT_VERIFIED` (as required: `TEST_DATABASE_URL` unavailable; skips recorded truthfully without inferring a pass).

### 3. Full Backend Pytest Suite
- **Command:** `'.venv\Scripts\python.exe' -m pytest -q`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Output:** `150 passed, 6 skipped, 1 warning in 10.88s`

### 4. Ruff Linter Check
- **Command:** `'.venv\Scripts\ruff.exe' check . ../dev`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Output:** `All checks passed!`

### 5. Ruff Format Check (Non-Mutating)
- **Command:** `'.venv\Scripts\ruff.exe' format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Output:** `6 files already formatted`

### 6. Alembic SQL Generation
- **Command:** `'.venv\Scripts\python.exe' -m alembic upgrade head --sql`
- **CWD:** `backend/`
- **Exit Code:** `0`
- **Output:** Valid SQL DDL generated, ending with:
```sql
-- Running upgrade 0006_bootstrap_trust_boundary -> 0007_oidc_pkce_browser_binding

ALTER TABLE oidc_states ADD COLUMN code_verifier VARCHAR(128);

ALTER TABLE oidc_states ADD COLUMN binding_digest VARCHAR(64);

UPDATE alembic_version SET version_num='0007_oidc_pkce_browser_binding' WHERE alembic_version.version_num = '0006_bootstrap_trust_boundary';

COMMIT;
```

### 7. Git Diff Check
- **Command:** `git diff --check`
- **CWD:** Repository root (`D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`)
- **Exit Code:** `0`
- **Output:** Empty (no whitespace errors or merge marker conflicts).

---

## 5. Process & Rule Compliance

- **No git discard commands:** No `git restore`, `git reset`, `git checkout`, or `git clean` was executed.
- **No environment variable probing:** No inspection of `TEST_DATABASE_URL` via echo, print, or environment tools.
- **No mutating formatters:** Only `ruff format --check` was executed; no mutating `ruff format` run.
- **No external network / daemon operations:** No Docker, Keycloak, or external services started.
- **Preserved workspace:** All existing dirty working-tree state was kept intact.

---

## 6. Remaining Limits & Handoff

- Dedicated live PostgreSQL tests (`tests/test_postgresql.py`) skipped (`NOT_VERIFIED`) due to unset `TEST_DATABASE_URL` in the environment.
- Live IdP (Keycloak) and browser E2E verification are out of scope for F1 and tracked in downstream tasks.
- Requesting independent review from Hermes Reviewer and OpenCode Tester.
