# CHPMIS-016-F1 — Migrate bootstrap integration regression to fixed trust source

## Identity and authority
- **Task ID:** CHPMIS-016-F1
- **Role:** Hermes Worker (sole product-code writer; this task is test-only) → OpenCode independent Verifier → separate Hermes Reviewer.
- **Mission trace:** CHPMIS-016, A3-01/A3-02, AC-05; existing protected-endpoint regression in `backend/tests/test_auth_remediation.py`.
- **Authorization:** The user's “Chạy big task tiếp theo” and “ok, cho phép và làm tiếp” authorize bounded work needed for CHPMIS-016. This follow-up only migrates an existing synthetic integration test to the approved fixed-source API; it does not approve host provisioning or broaden application behavior.
- **Status:** READY_FOR_WORKER. Preserve all existing dirty work; do not rewrite unrelated tests.

## Objective
Update only the existing bootstrap-to-protected-endpoint regression so it exercises the fixed registry-source test seam and cannot pass caller-selected approver keys. It must continue proving that bootstrap-created admins receive the canonical `system_admin` role and can call the protected endpoint.

## Allowed files
- `backend/tests/test_auth_remediation.py` — only import/helper/setup/assertion changes needed by `test_bootstrap_admin_session_recognized_by_protected_endpoint` and any narrowly scoped fixture helper required by that test.
- Append-only `.team/tasks/CHPMIS-016-F1-worker-report.md`.

No application code, other test files, migrations, configuration, runbooks, dependencies, host state, runtime, credentials, or unrelated content. Do not alter any other test in this file. If the fixed-source synthetic API cannot be exercised in this scope, stop and request a scoped review; do not add a compatibility path or production seam.

## Required behavior
- Seed only synthetic distinct Ed25519 keys into the in-memory registry test seam; all public keys used to verify approvals must be obtained through that seam.
- Build and sign the canonical payload shape expected by the fixed-source bootstrap API, using synthetic IDs and values.
- Do not pass or accept `approver_public_keys` (or any equivalent caller-selected trust argument).
- Keep the existing endpoint/session assertion and canonical role assertion intact.
- Keep test identities and key material ephemeral; no real agency data or secrets.

## Prompt template and plan
- Use the real prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, located through the installed prompt-lookup skill; adapt it to a minimal test-only migration with no product implementation.
- Follow the fixed-source Candidate C contract in `.team/tasks/CHPMIS-016-bootstrap-trust-boundary.md` and `.team/tasks/CHPMIS-011-W9-HKLM-worker.md`.

## Verification
From `backend/` run only:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py::test_bootstrap_admin_session_recognized_by_protected_endpoint`
2. `.venv\Scripts\ruff.exe check tests/test_auth_remediation.py`
3. `.venv\Scripts\ruff.exe format --check tests/test_auth_remediation.py`

From repository root run only:
4. `git diff --check`

Report exact command, result, and exit code. Do not claim the full suite passes; CHPMIS-016 implementation remains in progress.

## Definition of Done
- The focused protected-endpoint regression passes using the synthetic fixed-source seam and has no caller-selected approver-key argument.
- Only the named test and append-only report are changed by this task; no unrelated existing edits are reverted.
- Verification evidence is recorded; independent verifier/reviewer and main CHPMIS-016 implementation remain pending.
