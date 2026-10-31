# CHPMIS-011 R1 — Independent Hermes Reviewer

- **Role:** Hermes Reviewer, read-only, separate default-profile Kanban card.
- **Status:** PENDING.
- **Worker:** `t_62f9eddf`, run #33, worker session `20261031_102703_d64ed5` (from Worker report/card metadata).
- **Tester:** OpenCode run `2026-10-31T03-40-21-verifier-chpmis-011-independent-test-evidence-76de`, `ses_e6ff4b3d3ffeUhzuFGoNdRKybn`, BLOCKED before checks with exact shell denial recorded in its stdout; no test result is attributed to it.
- **Requirements:** Read `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `.team/tasks/CHPMIS-011-worker-report.md`, the approved spec, implementation plan, `AGENTS.md`, `.team/CHARTER.md`, and `.team/ledger.md`.
- **Source files:** `compose.yaml`, `.env.example`, `dev/keycloak/realm.json`, `backend/app/config.py`, `backend/app/auth/oidc.py`, `backend/app/auth/models.py`, `backend/alembic/versions/0005_initial_admin_bootstrap.py`, `backend/app/auth/bootstrap_admins.py`, `backend/tests/test_oidc_client.py`, `backend/tests/test_admin_bootstrap.py`, `backend/tests/test_auth_oidc.py`, and the local runbook.

## Safety and scope

Read-only review only. Do not edit any source, tests, task documentation, index, HEAD, or branch. Do not stage/commit, install, access remote/production/agency provider, run Docker/container/daemon/env/password commands, or use wrappers. Do not rerun tests already reported by Worker or coordinator. Review current files directly because much of this repository baseline is historically untracked; report the source files actually inspected and do not present a Git diff as complete where it omits untracked files. If any operation is denied, record the exact output and stop that operation.

## Review focus

- Plan/spec/task-pack compliance and exact file scope.
- OAuth code exchange timeout, request shape, HTTP/error sanitization and absence of token/secret leakage; preserve state, nonce, issuer, audience, signature, session and cookie policy.
- Fixed Keycloak issuer/frontchannel and internal backchannel consistency; opt-in profile, loopback-only bindings, credential handling and synthetic-only realm.
- Bootstrap requires exactly two distinct active users and zero prior System Admin grants; two distinct Project Owner/Security Reviewer signatures bind to the exact environment and ordered target pair; forged/mismatched/replayed approvals fail; roles and receipt are atomic; ordinary `granted_by`/approval history is not falsified; receipt is append-only and non-replayable.
- Migration correctness and compatibility with existing data and normal grant/revoke routes; tests exercise substantive behavior rather than only mocks; runbook commands match Compose and CLI behavior.
- Report all findings with file:line, severity P1/P2/P3, impact, and concrete fix. Include strengths, all behaviors considered-and-set-aside (or an explicit empty list), and verdict `APPROVED` or `CHANGES_REQUESTED`. Do not fix code or dispatch another reviewer.

## Evidence state

- Worker reported: focused 25 passed, full backend 80 passed/1 skipped, Ruff and Alembic offline SQL passed, all exit 0. These remain Worker-reported until independent T1 completes.
- Coordinator independently ran focused (25 passed) and full backend (80 passed/1 skipped), both exit 0 with a pre-existing Starlette/httpx deprecation warning plus pytest cache `WinError 5` warning. Coordinator also ran Ruff check, Ruff format, Alembic offline SQL and `git diff --check`, all exit 0.
- Live Docker/Keycloak/PostgreSQL not run. The Worker report marks them `NOT_VERIFIED`; the Reviewer must not claim live runtime proof.
