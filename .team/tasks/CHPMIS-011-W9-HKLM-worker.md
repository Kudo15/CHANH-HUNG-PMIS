# CHPMIS-011 W9 — Implement approved HKLM trust source

- **Task ID:** CHPMIS-011-W9-HKLM
- **Role:** Hermes Worker (sole product-code writer)
- **Status:** CODE IMPLEMENTATION AUTHORIZED — user directed execution of the next big roadmap task (CHPMIS-016) on 2026-10-31. Host provisioning/runtime remain gated.
- **Authority:** Owner approved Candidate C HKLM trust-source design only; user's 2026-10-31 instruction authorizes the bounded code-only implementation in this pack. Do not mutate host state, Registry, accounts, or ACLs.
- **Trace:** CHPMIS-011 AC-05; `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`; `.team/tasks/CHPMIS-011-W2-credential-safety-correction.md`; `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md` Candidate C.
- **Prompt template:** Reuse the retrieved Feature coding template by Onyekachi Ibekwe, prompts.chat ID `cmp1fv5ac0001js04jbj3pxoa` (cited in the main task pack). Modernize as a Python/FastAPI Worker: inspect existing implementation, preserve scope, use observed RED→GREEN, handle errors safely, run only listed checks and report exact results. Do not add Hermes skill metadata for Codex skills.

## Objective

Implement W9 application behavior against the owner-approved fixed registry trust source and complete bounded synthetic unit coverage. Current checkout is broadly dirty; preserve every pre-existing edit. Work in the existing repository checkout because the approved implementation history and dirty baseline must remain available.

## Approved trust-source contract

- Fixed source only: `HKLM\\SOFTWARE\\CHPMIS011LocalSynthetic\\TrustedApprovers`, Windows 64-bit registry view. The only allowed `REG_BINARY` values are `ProjectOwnerEd25519PublicKey` and `SecurityReviewerEd25519PublicKey`, exactly 32 bytes each and distinct.
- The live CLI runs on Windows and must fail closed on non-Windows. Never accept a path, hive, registry view, or trusted key from CLI args, env, request payload, database, current working directory or caller. No file-store fallback, embedded key, or warning-only permission check.
- Before consuming keys, inspect owner/security descriptors for `HKLM\\SOFTWARE` and every fixed task-created ancestor/key in the 64-bit view. Validate expected protected task-key DACLs. Use `AccessCheck` with an impersonation token duplicated from the actual process primary token at `SecurityImpersonation`; apply Registry `GENERIC_MAPPING` and mapped masks. Fail closed if the actual CLI token can set values, create/delete subkeys or links, delete keys, or change DACL/owner on the trust key or relevant ancestors. Keep handles open across checks and exact-value reads. Require `RegQueryInfoKeyW.cValues == 2`, exact names/types/lengths, explicit `ulOptions=0`, and explicit `KEY_WOW64_64KEY` on every open. Reject API errors, collision, malformed values, unexpected ACEs/owners, wrong view or incomplete evidence.
- Do not run registry commands, inspect the real path, create accounts, change ACLs, elevate, start Docker, connect services, read/write `.env`, or perform live runtime. Tests must use synthetic in-memory API/registry fixtures. Unit evidence does not prove actual host ACLs or two-account isolation.
- Host provisioning, actual two-account validation and live runtime require a later concrete independently reviewed host-change runbook and separate owner authorization. Do not include executable registry mutation/cleanup commands in this task's runbook edits.

## Required behavior

Implement all W9 behaviors recorded in the W2 task pack: persistent random instance UUID; canonical action/environment/ordered subjects/instance/request/operator/issued/expiry payload; both signatures over identical canonical bytes; zero-skew UTC checks with validity >0 and <=24 hours; distinct configured keys; stdin-only bounded JSON signatures; no caller-selected trust material; active distinct users; zero-admin precondition; replay protection; atomic grants and receipt; preserve old receipt data; non-destructive migration after 0005; database-level receipt update/delete rejection for supported PostgreSQL; and truthful documentation of DB-owner bypass. Keep ordinary grant/OIDC behavior unchanged. Treat operator ID as a signed synthetic claim, not authenticated identity. Never print/store signatures, private keys or secrets.

## Allowed files

Modify only:

- `backend/app/config.py`
- `backend/app/auth/bootstrap_admins.py`
- `backend/app/auth/models.py`
- one next migration after `backend/alembic/versions/0005_initial_admin_bootstrap.py`
- `backend/tests/test_admin_bootstrap.py`
- `docs/runbooks/CHPMIS-011-local-oidc-bootstrap.md`
- append-only `.team/tasks/CHPMIS-011-worker-report.md`

Do not add files or alter dependencies, existing migrations, Compose, `.env.example`, unrelated tests, ordinary grant routes, global permissions, host security, other task docs, or unrelated working-tree content. If a new test file or other path is needed, stop and request a scoped task update before editing.

## TDD and checks

Use RED→GREEN for each change. First add failing tests and observe that they fail for the intended missing behavior, then implement the minimum. Cover untrusted key substitution, Windows/non-Windows behavior, exact registry path/view/mask/value parsing, ACL/token denial and errors, distinct keys, malformed stdin/redaction, instance and payload mismatch, future/expired/over-24-hour/boundary times, replay, receipt protection, migration preservation and injected mid-transaction rollback. Mocked API tests are synthetic evidence only; mark actual machine guarantees `NOT_VERIFIED`.

Run only these exact checks:

From `backend/`:

1. `.venv\\Scripts\\python.exe -m pytest -q tests/test_admin_bootstrap.py`
2. `.venv\\Scripts\\python.exe -m pytest -q`
3. `.venv\\Scripts\\ruff.exe check . ../dev`
4. `.venv\\Scripts\\ruff.exe format --check app/config.py app/auth/bootstrap_admins.py app/auth/models.py tests/test_admin_bootstrap.py`
5. `.venv\\Scripts\\python.exe -m alembic upgrade head --sql`

From repository root:

6. `git diff --check`

Report exact commands, exit codes, redacted evidence and unavailable checks. No Docker/live runtime or registry command is authorized in this task.

## Definition of Done and closeout

- W9 source and bounded tests satisfy the fixed-source contract without weakening it.
- Exact allowlist respected; existing work preserved; TDD RED and GREEN evidence recorded in append-only Worker report.
- All assigned checks reported truthfully; any actual host ACL/two-account/runtime evidence remains `NOT_VERIFIED`.
- Report requirement trace, changed files, risks/limits and recommended next gates.
- Finish the Hermes card with exactly one of `kanban_request_review`, `kanban_block`, or `kanban_complete`. When the scoped implementation is complete, request review and note that independent OpenCode testing and a separate Hermes Reviewer are still required. Do not claim CHPMIS-011 complete or W9 live acceptance PASS.
- No commit, stage, push, deployment, remote access, subagents, permissions changes, or work outside the task scope.
