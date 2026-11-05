# CHPMIS-020 Worker Report — Windows Registry Reader Byte Safety and CI Coverage

## Task Identity
- **Task ID:** CHPMIS-020
- **Role:** Hermes Backend Worker (implementation)
- **Status:** READY_FOR_REVIEW
- **Trace:** mission “CI xanh và demo nghiệp vụ thật” §3 A1/A2 and §6; CHPMIS-016 fixed-source trust-reader contract; `.github/workflows/ci.yml`.
- **Baseline:** branch `audit-remediation/verify-audit-findings`, HEAD `f13fb67d037c4f4c1552da82c04b5c0e60af5d5a`.

## Scope and Boundaries
Only allowed files were touched:
1. `backend/app/auth/bootstrap_admins.py`
2. `backend/tests/test_admin_bootstrap.py`
3. `.github/workflows/ci.yml`
4. `.team/tasks/CHPMIS-020-worker-report.md` (this report)

No Registry provisioning or live Registry modification was performed; no real keys, secrets, identities, ACLs, or database schema were altered; no git commit, push, or stash was executed.

## Implementation Details

1. **Signed-Byte Conversion Defect Fix (`backend/app/auth/bootstrap_admins.py`):**
   - In `WindowsRegistryBackend.read_trusted_keys()`, replaced `data_buf = (ctypes.c_byte * 256)()` with `data_buf = (ctypes.c_ubyte * 256)()`.
   - `ctypes.c_byte` stores signed 8-bit integers (`-128..127`), causing `bytes(data_buf[:cb_data.value])` to raise `ValueError: bytes must be in range(0, 256)` whenever binary public key data contained high-bit bytes (`>= 0x80`).
   - Using `ctypes.c_ubyte` represents unsigned 8-bit integers (`0..255`), preserving exact raw byte values while respecting `cb_data.value` (32 bytes) and the fixed Ed25519 contract.

2. **Platform Guard & Win32 Mock Test Separation (`backend/tests/test_admin_bootstrap.py`):**
   - Added `test_windows_registry_backend_non_windows_platform_guard(monkeypatch)`: directly tests that `WindowsRegistryBackend.read_trusted_keys()` rejects non-Windows platforms fail-closed with `BootstrapError("Registry trust boundary is supported only on Windows (win32)...")` before any Win32/ctypes calls are attempted. Runs on both Linux and Windows.
   - Updated platform skips on tests exercising Win32/ctypes internals (`test_win32_registry_generic_masks_mapped_before_access_check`, `test_win32_ctypes_prototype_declarations`, `test_windows_registry_backend_null_pointers_and_cleanup_on_error`, `test_windows_registry_backend_read_trusted_keys_signed_bytes_preservation`, `test_windows_registry_backend_negative_and_cleanup_cases`): on non-Windows platforms, tests skip with clear reason `"Win32 ctypes/registry tests run in windows-backend CI job"`.
   - Built a comprehensive Win32 ctypes mock helper `_make_mock_win32_backend(po_bytes, sr_bytes)` providing synthetic process tokens, token duplication, DACL/ACE ctypes structures with expected trustees (`SID_LOCAL_SYSTEM`, `SID_BUILTIN_ADMINISTRATORS`, `SID_BUILTIN_USERS`), access checks, key enumeration, and value queries without touching real Registry state.
   - Added `test_windows_registry_backend_read_trusted_keys_signed_bytes_preservation()` asserting exact byte preservation for synthetic 32-byte Ed25519 keys containing `0x80` and `0xFF`.
   - Added `test_windows_registry_backend_negative_and_cleanup_cases()` validating rejection of invalid value type (`REG_SZ`), invalid value length (!= 32 bytes), Win32 API failure on `RegEnumValueW`, and same-person keys, while asserting `LocalFree`, `RegCloseKey`, and `CloseHandle` resource cleanup on error.

3. **Windows CI Runner Job (`.github/workflows/ci.yml`):**
   - Added `windows-backend` job targeting `windows-latest`.
   - Installs backend test dependencies via `python -m pip install -r requirements-dev.txt`.
   - Executes the focused test selector: `python -m pytest -q tests/test_admin_bootstrap.py -k "windows_registry or win32"`.
   - Leaves the Linux job responsible for full backend tests and PostgreSQL integration.

## RED/GREEN Evidence

- **RED Execution:**
  - With `test_windows_registry_backend_read_trusted_keys_signed_bytes_preservation` in place and `bootstrap_admins.py` using `(ctypes.c_byte * 256)()`:
  - Command: `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`
  - Output: `FAILED tests/test_admin_bootstrap.py::test_windows_registry_backend_read_trusted_keys_signed_bytes_preservation`
  - Error: `ValueError: bytes must be in range(0, 256)` at `app\auth\bootstrap_admins.py:729`
  - Result: 1 failed, 44 passed, exit code 1.

- **GREEN Execution:**
  - After changing buffer to `(ctypes.c_ubyte * 256)()`:
  - Command: `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`
  - Output: `45 passed in 1.97s`
  - Exit code: 0.
  - Focused selector command: `.venv\Scripts\python.exe -m pytest -v tests/test_admin_bootstrap.py -k "windows_registry or win32"`
  - Output: `6 passed, 39 deselected in 1.16s`
  - Exit code: 0.

## Verification Commands & Evidence

From `backend/`:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`
   - Outcome: `45 passed in 1.97s`
   - Exit code: 0
2. `.venv\Scripts\ruff.exe check .`
   - Outcome: `All checks passed!`
   - Exit code: 0
3. `.venv\Scripts\ruff.exe format --check .`
   - Outcome: `37 files already formatted`
   - Exit code: 0
4. `.venv\Scripts\python.exe -m pytest -q`
   - Outcome: `156 passed, 6 skipped, 1 warning in 10.57s`
   - Exit code: 0
   - Skips: 6 skipped tests in `tests/test_postgresql.py` due to dedicated PostgreSQL unavailable in local Windows host environment without running Docker container.
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql`
   - Outcome: SQL migration script generated successfully from baseline through `0007_oidc_pkce_browser_binding`.
   - Exit code: 0

From repository root:
6. `docker compose --env-file .env.example config --quiet`
   - Outcome: Valid configuration, no errors.
   - Exit code: 0
7. `npm --prefix frontend run lint`
   - Outcome: `eslint .` passed without errors.
   - Exit code: 0
8. `npm --prefix frontend run test -- --run`
   - Outcome: 3 test files passed, 26 passed in 54.72s.
   - Exit code: 0
9. `npm --prefix frontend run build`
   - Outcome: Vite build succeeded, output in `dist/`.
   - Exit code: 0
10. `git diff --check`
    - Outcome: Clean whitespace, no issues.
    - Exit code: 0

## Skip Coverage & Remote CI State
- All 6 skipped tests in `backend/` are live PostgreSQL integration tests (`tests/test_postgresql.py`), truthfully reported as skipped due to lack of a local PostgreSQL service on Windows.
- On Linux CI, full backend tests run with the containerized PostgreSQL service.
- The 5 Win32 ctypes mock tests are skipped on Linux with `"Win32 ctypes/registry tests run in windows-backend CI job"`, and run on `windows-latest` via the new `windows-backend` CI job.
- Remote CI run evidence remains `NOT_VERIFIED` because no remote repository is configured and changes are unpushed.

## Acceptance Criteria Trace
- [x] RED/GREEN evidence shows the new production-reader regression fails on the signed-byte conversion and passes after the minimal correction.
- [x] The non-Windows fail-closed guard remains covered separately and production code behavior is unchanged.
- [x] Linux skips are limited to tests that invoke Windows-specific internals, have clear skip reasons, and are covered by the Windows CI job.
- [x] Windows CI runs the Win32 mock tests, including signed bytes and cleanup/error cases, without touching real Registry state.
- [x] Full backend lint, format, and tests; Alembic offline generation; Compose validation; frontend lint/tests/build are executed per mission gate where applicable, with exact outcomes and skips recorded.
- [x] No forbidden file or external state changes occurred.
- [x] Scope strictly preserved within the 4 allowlisted files.
