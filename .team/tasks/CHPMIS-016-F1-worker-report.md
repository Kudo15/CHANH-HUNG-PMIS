# CHPMIS-016-F1 Worker Implementation Report

- **Task ID:** CHPMIS-016-F1 (Kanban task `t_1217842c`)
- **Role:** Hermes Worker (test-only migration)
- **Status:** MIGRATION COMPLETE / READY FOR INDEPENDENT VERIFIER & REVIEWER
- **Trace:** CHPMIS-016, A3-01/A3-02, AC-05; `backend/tests/test_auth_remediation.py`
- **Required Real Prompt Template:**
  - Source: prompts.chat, “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`
  - Modernized task-specific adaptation: “Act as a senior Python/FastAPI/SQLAlchemy engineer. Within the allowed test path (`backend/tests/test_auth_remediation.py`), migrate `test_bootstrap_admin_session_recognized_by_protected_endpoint` from the legacy caller-selected `approver_public_keys` invocation to the approved fixed-source synthetic registry seam (`SyntheticRegistryBackend`). Build and sign the canonical payload expected by the fixed-source bootstrap API, seed ephemeral synthetic Ed25519 keys into the in-memory registry test seam, verify that canonical `system_admin` role assignment and protected endpoint access succeed, and preserve all other tests and dirty work. Run only the 4 specified verification commands and record exact evidence in `.team/tasks/CHPMIS-016-F1-worker-report.md`.”

---

## 1. Scope and File Compliance

Worker modified or authored only the allowlisted files:
1. `backend/tests/test_auth_remediation.py`:
   - Updated imports to load `REG_BINARY`, `REGISTRY_NAMESPACE_PATH`, `REGISTRY_ROOT_PATH`, `REGISTRY_TRUST_KEY_PATH`, `VAL_PROJECT_OWNER`, `VAL_SECURITY_REVIEWER`, `SyntheticRegistryBackend`, `bootstrap_initial_admins`, `create_canonical_payload`, and `get_or_create_instance_state` from `app.auth.bootstrap_admins`.
   - Updated `generate_ed25519_keypair()` to return `(priv, pub_bytes)` containing raw 32-byte Ed25519 public key bytes.
   - Added helper `make_valid_synthetic_registry(po_bytes: bytes, sr_bytes: bytes) -> SyntheticRegistryBackend` scoped immediately above the integration test.
   - Migrated `test_bootstrap_admin_session_recognized_by_protected_endpoint`:
     - Creates ephemeral synthetic Ed25519 keys for Project Owner and Security Reviewer.
     - Seeds public keys into `SyntheticRegistryBackend` at `REGISTRY_TRUST_KEY_PATH` under `VAL_PROJECT_OWNER` and `VAL_SECURITY_REVIEWER` with valid DACL metadata.
     - Obtains `instance_id` from authoritative database singleton state (`get_or_create_instance_state(db)`).
     - Formats payload with `action="bootstrap_initial_admins"`, `environment="development"`, `target_subs`, `instance_id`, `request_id`, `operator_id`, `issued_at`, and `expires_at`.
     - Generates canonical JSON payload bytes via `create_canonical_payload` and signs with dual Ed25519 private keys.
     - Invokes `bootstrap_initial_admins(db, payload_data=payload_data, approvals=..., now=now, _registry_backend=backend)` without passing `approver_public_keys` or any caller-selected trust argument.
     - Preserved canonical role assertions (`"system_admin" in roles`, `Role.SYSTEM_ADMIN.value in roles`) and protected HTTP endpoint assertion (`client.get("/api/v1/auth/roles/system-admin/requests")` returning status 200 with `"requests"`).
2. `.team/tasks/CHPMIS-016-F1-worker-report.md`:
   - Authored this report.

No application code, other test files, migrations, configuration, runbooks, dependencies, host state, runtime, credentials, or unrelated content was modified. All existing dirty and untracked work was preserved untouched. No commits were made.

---

## 2. Verification Evidence

### Check 1: Focused regression test
**Command executed:**
```
cd backend && .venv/Scripts/python.exe -m pytest -q tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint
```
**Output:**
```
.                                                                        [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS\backend\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 1 warning in 1.18s
```
**Exit code:** `0`

### Check 2: Ruff check
**Command executed:**
```
cd backend && .venv/Scripts/ruff.exe check tests/test_auth_remediation.py
```
**Output:**
```
All checks passed!
```
**Exit code:** `0`

### Check 3: Ruff format check
**Command executed:**
```
cd backend && .venv/Scripts/ruff.exe format --check tests/test_auth_remediation.py
```
**Output:**
```
1 file already formatted
```
**Exit code:** `0`

### Check 4: Git diff check
**Command executed:**
```
git diff --check
```
**Output:**
```
(empty - no whitespace or diff errors)
```
**Exit code:** `0`

---

## 3. Definition of Done Checklist
- [x] The focused protected-endpoint regression passes using the synthetic fixed-source seam and has no caller-selected approver-key argument.
- [x] Only the named test and append-only report are changed by this task; no unrelated existing edits are reverted.
- [x] Verification evidence is recorded; independent verifier/reviewer and main CHPMIS-016 implementation remain pending.
- [x] No commit, stage, push, runtime, or host operations performed.
