# CHPMIS-016 — Bootstrap trust boundary (code-only implementation)

## Identity and authority
- **Task ID:** CHPMIS-016
- **Role:** Hermes Worker (sole product-code writer) → OpenCode independent Verifier → separate Hermes Reviewer
- **Mission trace:** A3-01/A3-02, AC-05; Task 4 in `docs/superpowers/plans/2026-10-31-audit-remediation.md`.
- **Detailed implementation contract:** `.team/tasks/CHPMIS-011-W9-HKLM-worker.md`; read it with the main CHPMIS-011 pack, W2 correction, Candidate C design in `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md`, `OPEN_QUESTIONS.md`, `AGENTS.md`, `.team/CHARTER.md`, and `.team/ledger.md`.
- **Authorization:** User directed “Chạy big task tiếp theo” after the roadmap identified CHPMIS-016. This authorizes only bounded application-code and synthetic-unit-test work in W9. It does not authorize Registry inspection/provisioning, accounts, ACL changes, elevation, live services, real identities/approvers, production, or deployment.
- **Status:** COMPLETE for the bounded local synthetic implementation and verification. OpenCode retry passed all six exact W9 checks after the owner-authorized exact shell rules; Hermes Reviewer approved the final F2 trust-boundary fixes. Host Registry owner/DACL, account/identity custody, live runtime, agency IdP, production, and remote CI remain NOT_VERIFIED. Evidence: `.team/tasks/CHPMIS-016-F2-opencode-verifier.md`. Owner decision (2026-11-01): shared HKLM `SOFTWARE` gets effective-rights checks only; task-created CHPMIS keys must be owned by `BUILTIN\Administrators`.


## Objective
Implement the approved local synthetic bootstrap trust boundary in application code: read only the fixed HKLM 64-bit source, fail closed on unsupported or unsafe conditions, verify exact approver keys and signed bootstrap payload, and preserve approved one-time atomic bootstrap/receipt behavior. Mock tests are not proof of host ACL safety or human independence.

## Allowed files
Use exactly the W9 allowlist:
- `backend/app/config.py`
- `backend/app/auth/bootstrap_admins.py`
- `backend/app/auth/models.py`
- One next Alembic migration after `backend/alembic/versions/0005_initial_admin_bootstrap.py`
- `backend/tests/test_admin_bootstrap.py`
- `docs/runbooks/CHPMIS-011-local-oidc-bootstrap.md`
- Append-only `.team/tasks/CHPMIS-011-worker-report.md`

No new files, dependency edits, existing-migration edits, Compose or `.env.example` changes, ordinary grant routes, global permissions/configuration, host security, registry commands, accounts, ACLs, Docker, live providers, or unrelated worktree content. CHPMIS-016-F1 migrated the existing integration test to the synthetic fixed-source API; it does not add `test_auth_remediation.py` to this implementation pack. Resume this unchanged product-code allowlist. Caller-supplied key arguments, compatibility branches, fallbacks, and other externally selected trust material are forbidden. If another path is required or the contract cannot be met safely, stop for a scoped review; do not expand the allowlist.

## Required behavior
Implement the complete fixed-source contract in the W9 pack, including:
- Fixed `HKLM\\SOFTWARE\\CHPMIS011LocalSynthetic\\TrustedApprovers`, explicit 64-bit view and exactly two `REG_BINARY` public keys; never accept caller-selected trust material or fall back to file, environment, database, or embedded keys.
- Before consuming keys, validate relevant owner/DACL and effective rights using the actual process token, duplicated impersonation token, Registry `GENERIC_MAPPING`, and fail-closed API handling. Keep handles open through checks and reads; reject wrong view, unexpected values/count/types/lengths/ACEs, incomplete ACL data, and API errors.
- Preserve signed environment/ordered-target/instance/request/operator/time binding, distinct configured keys, bounded stdin-only signatures, UTC validity ≤24 hours, replay denial, zero-admin precondition, active distinct users, atomic grants and receipt, append-only receipt protection, and migration compatibility.
- Preserve OIDC/session and normal role-grant behavior. Do not claim the two keys prove two real people; official nominations, custody, identities, and production remain gated.

## TDD and verification
Use only `backend/tests/test_admin_bootstrap.py` for tests. Begin with focused RED tests for registry source/path/view/access mask/value validation, ACL/token denials/API errors, key distinction, malformed/signature-input redaction, payload/instance/time/replay boundaries, receipt protection, migration preservation, and injected transaction rollback. Observe intended failures before code, then GREEN.

Run only the W9 checks:

From `backend/`:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check app/config.py app/auth/bootstrap_admins.py app/auth/models.py tests/test_admin_bootstrap.py`
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql`

From repository root:
6. `git diff --check`

Report exact commands, outputs, and exit codes. Stop on failure without weakening tests. No live/runtime/host checks are allowed. Real host trust-store, two-account, and runtime guarantees remain `NOT_VERIFIED`.

## Prompt template and plan
- Reuse the real prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, previously located/retrieved via prompt-lookup; citation and W9 adaptation are in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md` and the W9 pack.
- Follow Candidate C and the bounded implementation sequence in `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md`; Task 4 in the audit remediation plan points to this design. Preserve review precision notes on `AccessCheck`, process-token duplication, Registry `GENERIC_MAPPING`, `RegQueryInfoKeyW.cValues == 2`, exact names/types/lengths, `REG_CREATED_NEW_KEY`, `ulOptions=0`, and `KEY_WOW64_64KEY`.

## Definition of Done
- RED→GREEN evidence and append-only Worker report are complete.
- Only the allowlist changed; parent task checks pass or are explicitly `NOT_VERIFIED`.
- OpenCode independently reruns assigned checks; separate Hermes Reviewer approves the final diff.
- Report synthetic code/test results separately from forbidden/unverified host provisioning, account isolation, live runtime, agency IdP, and production.
- No commit, stage, push, deployment, remote access, or host mutation.
