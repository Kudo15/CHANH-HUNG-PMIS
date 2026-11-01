# CHPMIS-016-F2 — Close owner, DACL/ACE, and Win32 binding review findings

## Identity and authority
- **Task ID:** CHPMIS-016-F2
- **Role:** Hermes Worker (sole product-code writer) → OpenCode independent Verifier → separate Hermes Reviewer.
- **Trace:** CHPMIS-016 / CHPMIS-011 W9; R1 findings in `.team/tasks/CHPMIS-016-R1-hermes-reviewer.md`; audit A3-01/A3-02 and AC-05.
- **Authorization:** Continues the user's authorization for the bounded CHPMIS-016 code-only task. It implements the already approved Candidate C ACL model for synthetic application code; it does not authorize host provisioning or runtime.
- **Status:** COMPLETE — owner decision received 2026-11-01; implementation, all six OpenCode checks, and independent Hermes review are complete. User-authorized exact shell rules and verification outputs are recorded in `.team/tasks/CHPMIS-016-F2-opencode-verifier.md`. Wildcard shell deny and edit deny remain.


## Objective
Close R1's fixed-source assurance gaps using the approved task-key security descriptor, and make all Windows API bindings pointer-size safe. Preserve fixed-source behavior and all CHPMIS-016 business/data semantics.

## Required changes

1. **Owner SID:** Extract and validate the owner SID from each task-created key descriptor (`SOFTWARE\\CHPMIS011LocalSynthetic` and `...\\TrustedApprovers`), requiring `BUILTIN\\Administrators` (`S-1-5-32-544`). At the pre-existing shared `HKLM\\SOFTWARE` root, validate effective rights only; do not require or allowlist its owner SID. Fail closed on missing/invalid owner evidence for task-created keys.
2. **Task-key DACL/ACE:** For task-created keys, validate a protected DACL against the approved exact SDDL `O:BA G:SY D:P(A;;KA;;;SY)(A;;KA;;;BA)(A;;KR;;;BU)` (or an explicitly equivalent structural form). Enumerate and reject unexpected, malformed, inherited, deny, callback, or extra grant ACEs. For `HKLM\\SOFTWARE`, check descriptor completeness and prohibited effective rights only; do not impose the task-key SDDL or an owner allowlist on this shared root.
3. **Effective rights:** Use the actual process primary token duplicated to `SecurityImpersonation`; define/use Registry `GENERIC_MAPPING`, map desired masks before `AccessCheck`, and fail closed on errors or incomplete privilege/ACL evidence. Preserve read handles through checks and exact value reads.
4. **ctypes:** Declare explicit `argtypes` and pointer-sized `restype` for every Win32 function called. Use correctly typed/sign-extended predefined HKEY constants and pointer/handle types. Keep error and resource cleanup paths safe; synthetic tests must not call the real host Registry.
5. **Synthetic coverage:** Extend only `backend/tests/test_admin_bootstrap.py` to exercise owner accept/reject, exact DACL and ACE accept/reject, generic masks, API argument/return type declarations, invalid/null pointers, and cleanup on API errors. Keep the approved synthetic test seam, distinct ephemeral keys, and no host calls.

## Allowed files
- `backend/app/auth/bootstrap_admins.py`
- `backend/tests/test_admin_bootstrap.py`
- Append-only `.team/tasks/CHPMIS-011-worker-report.md`

No other source/tests/config/migration/runbook/task docs, dependencies, global permissions, host Registry, ACL/accounts, elevation, Docker, live service, real identity or production. Existing dirty work must be preserved. If the root-owner policy is still unresolved or a faithful safe check cannot be implemented within these files, stop and `kanban_block`; do not weaken the trust boundary.

## TDD and prompt template
- Before production edits, write separate behavioral RED tests for owner and DACL/ACE checks, mapped access masks, and ctypes prototype correctness. Observe each intended failure before changing implementation.
- Reuse the real prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`; task-specific modernization is recorded in CHPMIS-016 and this follow-up.
- Follow `superpowers:test-driven-development` and the R1 evidence. Do not attempt a Windows host API probe; use deterministic fake API boundaries only.

## Verification
Run only the exact parent W9 commands after the complete focused implementation is ready:
1. From `backend/`: `.venv\\Scripts\\python.exe -m pytest -q tests/test_admin_bootstrap.py`
2. From `backend/`: `.venv\\Scripts\\python.exe -m pytest -q`
3. From `backend/`: `.venv\\Scripts\\ruff.exe check . ../dev`
4. From `backend/`: `.venv\\Scripts\\ruff.exe format --check app/config.py app/auth/bootstrap_admins.py app/auth/models.py tests/test_admin_bootstrap.py`
5. From `backend/`: `.venv\\Scripts\\python.exe -m alembic upgrade head --sql`
6. From repository root: `git diff --check`

Report exact commands, outputs, and exit codes, including any required test failures. No host/runtime verification is allowed.

## Owner amendment (2026-11-01)

The user explicitly authorized OpenCode shell execution to continue this task. Coordinator added only these exact rules to `C:\Users\ANHVU\.config\opencode\agents\role-verifier.md`:
- `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`
- `.venv\Scripts\ruff.exe format --check app/config.py app/auth/bootstrap_admins.py app/auth/models.py tests/test_admin_bootstrap.py`

The role's wildcard shell deny and edit deny were verified unchanged. This user instruction is a narrow exception to the earlier task-pack prohibition; no other permission rule or host/runtime boundary changed.

## Definition of Done
- All R1 findings are fixed or receive a technically justified, independently reviewed resolution consistent with the approved design.
- RED/GREEN evidence and append-only report are complete; only the allowlist changed.
- Exact Worker checks pass; OpenCode verifier and a separate Hermes Reviewer provide independent results, or verifier is truthfully `NOT_VERIFIED` and task stays open.
- Actual Registry owner/DACL, account isolation, runtime, identities, and production remain `NOT_VERIFIED` until separately authorized.
