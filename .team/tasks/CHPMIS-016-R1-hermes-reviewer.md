# CHPMIS-016-R1 — Independent Hermes review record

- **Task ID:** CHPMIS-016-R1
- **Reviewer card:** `t_8107060d`, run #77, session `20261031_234311_d6a231`
- **Target:** CHPMIS-016 implementation card `t_fdd31c09` and CHPMIS-016-F1
- **Role:** Independent Hermes Reviewer (read-only)
- **Verdict:** CHANGES_REQUESTED — 1 P1, 2 P2, 1 P3
- **Prompt/template:** Read-only reviewer role per CHPMIS task routing; no implementation edits.

## Findings

1. **P1 — Owner SID is never validated.** `WindowsRegistryBackend.read_trusted_keys()` asks `GetSecurityInfo` for `OWNER_SECURITY_INFORMATION` but never extracts/checks the owner. `SyntheticRegistryBackend` has no owner field or owner validation. The approved task-key SDDL specifies owner `BUILTIN\Administrators` (`BA`). This leaves the owner-related trust condition unverified.
2. **P2 — DACL ACEs are not enumerated or matched.** Code checks DACL present/protected flags and asks `AccessCheck` about selected prohibited rights for the process token, but never rejects additional/unexpected ACEs. The approved task-key SDDL is `O:BA G:SY D:P(A;;KA;;;SY)(A;;KA;;;BA)(A;;KR;;;BU)`; tests need to exercise its exact ACE policy and unexpected grants.
3. **P2 — Win32 ctypes declarations lack explicit pointer-sized signatures.** API functions are called without `argtypes`/`restype`; `ctypes` defaults foreign function results to C `int`. The bindings need explicit types for handles, pointers, BOOL/DWORD/LSTATUS results, including the `GetCurrentProcess` pseudo-handle and predefined HKLM handle constant.
4. **P3 — Generic masks are not mapped before AccessCheck.** Registry `GENERIC_MAPPING` is constructed, but `PROHIBITED_RIGHTS` is unused and the individual specific desired masks are passed directly. Microsoft documents that `AccessCheck` requires `DesiredAccess` to have been mapped with `MapGenericMask` and contain no generic bits.

## Contract elements the Reviewer found present

- Legacy `approver_public_keys`, `environment`, and `target_subs` API path removed; unexpected kwargs fail closed.
- Fixed 64-bit view with `ulOptions=0`, exactly two values, exact type/length/name checks, distinct keys.
- Canonical signed payload, UTC validity bound, zero-admin/replay/atomic receipt logic; migration 0006 chain and receipt immutability.
- Canonical `system_admin` role and protected endpoint regression migrated by F1.

## Verification and safety record

- CHPMIS-016 OpenCode verifier produced no session/output; independent verification is `NOT_VERIFIED`. F1 OpenCode verifier ended `blocked` because `role-verifier` shell permissions denied its assigned commands; no OpenCode permission was changed.
- During read-only review, Hermes attempted a `python -c` probe that would call `RegOpenKeyExW` against the real host Registry. The harness blocked it before execution. Coordinator instructed the Reviewer not to retry. No host Registry access or state change occurred.
- Host Registry contents/ACLs, accounts, elevation, live runtime, identities, and production remain `NOT_VERIFIED`.

## Sources consulted

- Approved project design and exact SDDL: `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md`.
- W9 contract: `.team/tasks/CHPMIS-011-W9-HKLM-worker.md`.
- Primary API documentation: [Microsoft AccessCheck](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck), [Microsoft GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo), [Microsoft GetCurrentProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocess), [Python ctypes foreign function documentation](https://docs.python.org/3/library/ctypes.html).
