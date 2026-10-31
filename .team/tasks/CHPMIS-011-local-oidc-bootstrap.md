# CHPMIS-011 — Local OIDC and initial System Admin bootstrap

- Owner authorization: design explicitly approved on 2026-10-31; proceed with implementation and local synthetic verification.
- Roles: Codex Coordinator/Planner; Hermes Worker; independent OpenCode Tester; separate Hermes Reviewer. Inherit each harness's configured defaults, no model/provider overrides; run sequentially in the existing dirty checkout.
- Status: IN PROGRESS.
- Trace: AC-05; current CHPMIS-010 head `0004_projects_tasks_audit`; approved local Keycloak + one-time offline two-person bootstrap design.
- Role contract: Worker implementation only. Read this pack first and implement the bounded plan; do not dispatch helpers/reviewers, commit, stage, push, deploy, or alter any files outside the allowlist. Work in the existing repo checkout and preserve every pre-existing change. Post progress and finish the Hermes card with exactly one of `kanban_complete`, `kanban_request_review`, or `kanban_block`, including exact evidence and concerns.
- Approved design: `docs/superpowers/specs/2026-10-31-chpmis-011-local-oidc-bootstrap-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md`.

## Objective and scope

Implement a synthetic local Keycloak provider and real OIDC token exchange, then an offline, one-time bootstrap command for exactly two initial System Admin users, with independent Project Owner and Security Reviewer approvals and a durable append-only receipt. Verify the provider round-trip against the task's isolated local Keycloak and disposable PostgreSQL environment. Do not connect an agency IdP, use real identities, or deploy.

## Worker file scope

Worker may modify only:

- `compose.yaml`, `.env.example`, and new synthetic-only assets under `dev/keycloak/`.
- `backend/app/config.py`, `backend/app/auth/oidc.py`, `backend/app/auth/models.py`.
- The next Alembic migration after the checked current head, expected `backend/alembic/versions/0005_initial_admin_bootstrap.py`.
- New `backend/app/auth/bootstrap_admins.py`.
- `backend/tests/test_oidc_client.py`, `backend/tests/test_admin_bootstrap.py`, and narrowly scoped updates to `backend/tests/test_auth_oidc.py`.
- Narrow synthetic-credential generator regression tests under `backend/tests/` when required by W2/W3 follow-up.
- New runbook `docs/runbooks/CHPMIS-011-local-oidc-bootstrap.md`.
- Worker evidence report `.team/tasks/CHPMIS-011-worker-report.md`.

Do not change ordinary grant/revocation routes or policy, other migrations, dependency manifests, CI, frontend, audit behavior, or business workflow. If dependency or schema history differs from plan, report the exact discrepancy before expanding scope. Do not overwrite CHPMIS-009's historical manifest.

Coordinator may maintain this task pack, `.team/tasks/CHPMIS-011-W2-credential-safety-correction.md`, `.team/tasks/CHPMIS-011-T1-test-evidence.md`, `.team/tasks/CHPMIS-011-R1-independent-review.md`, `.team/tasks/CHPMIS-011-R2-independent-review.md`, `.team/tasks/CHPMIS-011-runtime-evidence.md`, `.team/ledger.md`, `TASKS.md`, `PLAN.md`, `OPEN_QUESTIONS.md`, the approved design and implementation-plan documents, and `ACCEPTANCE.md`. Coordinator does not edit product/test code.

## Worker prompt and execution contract

Prompt template located through installed prompt-lookup and fully retrieved on 2026-10-31: **Feature coding template**, Onyekachi Ibekwe, prompts.chat ID `cmp1fv5ac0001js04jbj3pxoa`, [source](https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template). The source asks for feature implementation, idiomatic code, error handling, tests, docs, and a commit message. Modernized for this task: act as a Python/FastAPI Worker; read the repo AGENTS/charter, this task pack, approved spec, plan and ledger; inspect the exact current migration chain; use TDD with observed RED then GREEN; change only the allowlist; preserve existing state/nonce/signature/issuer/audience/session/security behavior; add bounded, sanitized token exchange and a synthetic loopback-only Keycloak profile; implement a one-time offline bootstrap with two distinct Ed25519 approval keys, payload binding to exact environment and ordered target pair, zero-admin precondition, active/distinct targets, atomic role+receipt writes, replay rejection and no fake ordinary grant provenance; update the runbook; run only listed checks; provide exact commands/results, files, redacted errors and a recommended commit message; do not commit, stage, deploy, push, access remotes, add subagents, broaden scope, or claim live verification without captured runtime evidence.

Use `superpowers:test-driven-development`: each new behavior starts with a focused failing test, record why it failed, implement the smallest change, then rerun focused and full checks. Do not write production code before observing RED. Coordinator only issues a scoped correction task; Worker is the sole product-code writer.

## Approved architecture and constraints

- Official Keycloak image pinned to `quay.io/keycloak/keycloak:26.8.1` (official release verified 2026-10-31); opt-in Compose profile `local-oidc`, fixed browser issuer on loopback, internal Compose backchannel for token/JWKS, synthetic realm/client only.
- Host-published services must bind to `127.0.0.1`. Use task-specific generated process-only credentials; never print or commit secrets. No real organization data, groups, claims, provider credentials, or identities.
- Preserve existing OIDC state/nonce one-time use, signature verification, issuer/audience checks, session cookie/CSRF policy, and all ordinary System Admin request/revoke behavior.
- `DefaultOIDCClient.exchange_code(code, redirect_uri)` must use a bounded timeout; errors/logs must not reveal code, token response, client secret, or credentials.
- Bootstrap is a one-time CLI outside HTTP routes. It accepts exactly two distinct active, already OIDC-authenticated target users and exactly two separately configured approver public keys (Project Owner and Security Reviewer); both signatures must bind the same canonical payload containing environment and exact ordered target subject pair. Require zero existing System Admin grants; write both grants and an append-only receipt in one transaction; reject malformed/forged/duplicate/stale/mismatched/replayed approvals and rollback atomically. Never invent `granted_by` or ordinary grant/approval history. Private keys remain external/process-only. Receipt must not contain personal names/emails, signatures, tokens, or secrets.
- This approved local design does not approve actual agency IdP, official approver nominations/key custody, real identities, production grant, deployment or remote access. Keep those in `OPEN_QUESTIONS.md` for a later Human Gate.
- Preserve the dirty working-tree baseline and existing services/volumes. Use Compose project `chpmis011`; never stop, remove, reset, or reuse `chpmis010` services or volume. Stop only `chpmis011` containers after evidence and preserve its named volume unless the task's isolated runtime creates none.
- No staging/commit/push/merge/deploy or unrelated global permissions/configuration changes. On 2026-10-31 the owner explicitly authorized a narrow exception: the Coordinator may update and reload the OpenCode `role-verifier` agent's shell permissions so it can perform T1; the Tester must not alter permissions itself.

## Verification commands

From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_oidc_client.py tests/test_auth_oidc.py tests/test_admin_bootstrap.py tests/test_synthetic_credentials.py`
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check app/config.py app/auth/oidc.py app/auth/models.py app/auth/bootstrap_admins.py tests/test_oidc_client.py tests/test_auth_oidc.py tests/test_admin_bootstrap.py tests/test_synthetic_credentials.py ../dev/keycloak/generate_synthetic_credentials.py`
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql`

From repository root:

6. `docker --context desktop-linux compose --project-name chpmis011 --profile local-oidc --env-file .env.example config --quiet` with required local synthetic values supplied only as process-local environment overrides; never print their values.
7. Isolated live Keycloak/PostgreSQL OIDC and bootstrap smoke commands exactly as recorded in `docs/runbooks/CHPMIS-011-local-oidc-bootstrap.md` after Worker defines them. Record every exact command, output summary, and exit code. Verify actual published bindings are loopback, login produces a session without role on first login, invalid state/nonce fails, two approvals bind to target/environment, both roles and receipt commit atomically, and replay is rejected.
8. `git diff --check`.

Do not rely on the live checks until their exact commands exist in the runbook. If Docker cannot run or any command is denied, record `NOT_RUN`/`NOT_VERIFIED`, exact observed reason, and continue independent source/unit checks without workarounds or permission changes.

## Independent Tester and Reviewer

- OpenCode Tester is read-only and independently runs checks 1–5 and 8, inspecting only the scoped diff/task pack. It may run the local live provider checks only if explicitly present in its assigned allowed command list and permissions; never change its permission config. If shell is denied, report BLOCKED and await user direction.
- Hermes Reviewer is independent/read-only. Inspect the complete scoped diff and worker report against acceptance, migration/provenance safety, transaction/replay behavior, loopback binding, token/error redaction, OIDC validation preservation, and task-file scope. Reviewer may not modify code, rerun destructive/live runtime actions, or use unrelated Docker projects. Use a separate Hermes card and no overrides.
- Record exact harness, role, run/card/session identifiers, status, exit, GUI visibility, exact model/provider/profile/metrics only when exposed; unknown is `không có dữ liệu`, never zero.

## Owner-approved follow-up scope — local synthetic bootstrap hardening

The owner approved the local synthetic hardening objectives and 24-hour maximum on 2026-10-31; see `OPEN_QUESTIONS.md` and the follow-up plan. No real identity/provider, production access or real trust-custody policy is approved. R3/R5 findings and the Coordinator's safety assessment are in `.team/tasks/CHPMIS-011-R2-independent-review.md`.

A bounded Hermes Worker may implement W9 only after the owner separately authorizes code implementation; design approval alone is insufficient. The self-contained proposed Worker pack is `.team/tasks/CHPMIS-011-W9-HKLM-worker.md`. Its proposed allowed files are limited to `backend/app/config.py`, `backend/app/auth/bootstrap_admins.py`, `backend/app/auth/models.py`, one next Alembic migration after `0005`, `backend/tests/test_admin_bootstrap.py`, the CHPMIS-011 runbook, and append-only `.team/tasks/CHPMIS-011-worker-report.md`. Do not add a new test file without first expanding this allowlist and its exact verification command. `.env.example` may be changed for non-secret variable names/placeholders only if required; `compose.yaml`, existing migrations, dependencies, ordinary grant routes, other tests and all other files remain outside this follow-up. Trust-store contents and private keys must not be committed or hardcoded.

**W9 verification commands:** From `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_admin_bootstrap.py`; `.venv\Scripts\python.exe -m pytest -q`; `.venv\Scripts\ruff.exe check . ../dev`; `.venv\Scripts\ruff.exe format --check app/config.py app/auth/bootstrap_admins.py app/auth/models.py tests/test_admin_bootstrap.py`; `.venv\Scripts\python.exe -m alembic upgrade head --sql`. From repository root: `git diff --check`. Worker must report exact exit codes and any environment limitation. Do not run Docker, live Keycloak/PostgreSQL, registry commands, or host account/ACL checks.

The W9 trust-source design is owner-approved **for design only** in Candidate C of `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md`, after Hermes Reviewer run #58. Separate owner authorization is still required before dispatching auth/trust-source code implementation. The proposed implementation contract is in `.team/tasks/CHPMIS-011-W2-credential-safety-correction.md`. The only proposed live source is HKLM 64-bit `HKLM\SOFTWARE\CHPMIS011LocalSynthetic\TrustedApprovers`; the Windows-host CLI must validate owner/DACL and effective access using the actual process token and fail closed. Synthetic registry/API fixtures are allowed in unit tests only. Do not inspect or modify the real registry, create accounts, change ACLs, elevate, or run live runtime. Preserve old receipts and do not authorize destructive downgrades; use process-memory/stdin signature input without printing or disk files. Do not claim two keys prove two real people. Actual provisioning, two-account OS verification and live Docker/Keycloak/bootstrap remain separate gates requiring a concrete independently reviewed host-change runbook and explicit owner authorization.

## Definition of Done

- OIDC exchange unit tests and full backend tests pass; Ruff and Alembic offline upgrade verification pass, or any unavailable check is explicitly `NOT_VERIFIED`.
- Isolated live Keycloak round-trip and disposable PostgreSQL bootstrap smoke pass, or a truthful `PARTIAL / NOT_VERIFIED` result identifies the blocked AC; no fabricated runtime evidence.
- Bootstrap invalid/replay/transaction cases are covered; regular dual-admin grants remain unchanged.
- OpenCode independently reports scoped test results; Hermes Reviewer returns `APPROVED` with no blocking findings. Required corrections receive TDD and scoped re-review.
- This task and acceptance/ledger record distinguish synthetic local proof from still-unverified agency IdP, real approvers/identities, browser-secure transport in an actual agency deployment, and production authorization.
