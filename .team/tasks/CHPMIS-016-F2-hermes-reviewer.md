# CHPMIS-016-F2 — Independent Hermes Reviewer Record

- **Task ID:** CHPMIS-016-F2-R1
- **Role:** Independent Hermes Reviewer (read-only)
- **Reviewer card:** `t_23d7ba0e`, run #79, session `20261101_053431_f1cae8`
- **Worker card:** `t_45bef3b1`, run #78, session `20261101_051954_71ecd9`
- **Scope:** `.team/tasks/CHPMIS-016-F2-owner-dacl-ctypes.md`; F2 changes in `backend/app/auth/bootstrap_admins.py`, `backend/tests/test_admin_bootstrap.py`, and append-only Worker report Section 15. No implementation edits or host API calls.
- **Requirement trace:** CHPMIS-016 / CHPMIS-011 W9; R1 findings P1 owner SID, P2 task-key DACL/ACE, P2 ctypes signatures, P3 generic access mapping; owner decision dated 2026-11-01.
- **Verdict:** **APPROVED — 0 P1, 0 P2, 0 P3 findings.**

## Findings disposition

- Task-created keys require `BUILTIN\Administrators` (`S-1-5-32-544`) owner; shared `HKLM\SOFTWARE` gets effective-rights checks only.
- Task-key DACLs require protected status and exactly three allow ACEs with the approved trustees and masks. Unexpected ACE types, flags, trustees, duplicates, and masks are rejected.
- `MapGenericMask` is applied before `AccessCheck`.
- Win32 functions have explicit `argtypes` and `restype`; the 64-bit `HKEY_LOCAL_MACHINE` constant is sign-extended. Error/null handling and resource cleanup were reviewed.
- Reviewer considered these changes sufficient to close each R1 finding for code/synthetic scope.

## Independent verification

Reviewer reran the six exact commands in the F2 pack:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py` — 42 passed, exit 0.
2. `.venv\Scripts\python.exe -m pytest -q` — 132 passed, 2 skipped, 1 warning, exit 0.
3. `.venv\Scripts\ruff.exe check . ../dev` — all checks passed, exit 0.
4. `.venv\Scripts\ruff.exe format --check app/config.py app/auth/bootstrap_admins.py app/auth/models.py tests/test_admin_bootstrap.py` — 4 files already formatted, exit 0.
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql` — SQL generated through migration `0006`, exit 0.
6. `git diff --check` — clean, exit 0.

## Process deviations and limits

- Worker attempted an ad hoc `python -c` probe. Harness blocked it before execution; no host Registry call occurred.
- Worker ran the unlisted `.venv\Scripts\ruff.exe format tests/test_admin_bootstrap.py` after the exact format check failed. It edited only the allowlisted test file. This command was outside the pack and is recorded as a process deviation.
- Reviewer attempted a local Hermes-log query using `python -c`; the harness blocked it before execution. The reviewer continued with available read-only source and task evidence; no implementation files were changed.
- OpenCode verifier run `2026-10-31T22-34-55-verifier-chpmis-016-f2-exact-independent-verifier-419c` produced no session ID or command output and remained `created`; its launcher was stopped after no progress. OpenCode independent verification is **NOT_VERIFIED**, and F2 stays open pending that gate.
- Host Registry owner/DACL state, host ACLs/accounts, elevation, live runtime, identities, and production remain **NOT_VERIFIED**.
