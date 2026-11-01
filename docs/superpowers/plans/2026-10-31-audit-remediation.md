# Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for each behavior change. Run only commands named in the active task pack. Follow its file allowlist and closeout rules.

**Goal:** Remediate the confirmed audit defects on baseline `a986d31063c52d0ea99cec164d8e5c58b1afa3e1`, verify them with regression tests and independent review, then gate synthetic E2E and the next multi-department slice.

**Architecture:** Preserve the Python/FastAPI + SQLAlchemy/Alembic backend, React/Vite frontend, PostgreSQL and opt-in local Keycloak. Codex acts as Coordinator/Planner; one Hermes Worker edits an explicitly listed scope at a time; OpenCode runs the independent read-only Tester; a separate Hermes session reviews after testing. Local development remains loopback-only and synthetic. The current fixed HKLM candidate is a local design only; this plan does not authorize registry/ACL/account mutation, real identities, agency IdP, production or deployment.

**Execution order:** CHPMIS-014 canonical bootstrap role → CHPMIS-013 schema/migration/CI → CHPMIS-015 admin transaction/concurrency → CHPMIS-016 fixed synthetic bootstrap trust source → CHPMIS-017 endpoint authorization matrix → CHPMIS-012 browser OIDC/authenticated local E2E → CHPMIS-018 PostgreSQL project/task consistency → CHPMIS-019 frontend state/error/date defects. CHPMIS-012 and CHPMIS-013 were already reserved in `PLAN.md`; IDs are not reused. The order may be refined only after evidence and without overlapping workers on shared files. C-phase department slice remains behind the platform gate.

## Task 1 — CHPMIS-014 canonical System Admin bootstrap key

**Files:** `backend/app/auth/bootstrap_admins.py`, `backend/tests/test_admin_bootstrap.py`, `backend/tests/test_auth_remediation.py`, append-only `.team/tasks/CHPMIS-014-worker-report.md`.

1. Add a failing integration test: bootstrap two synthetic existing users, validate the resulting session, then request the protected System Admin request-list endpoint over HTTP.
2. Run the focused test and record the exact RED caused by the display-label/canonical-key mismatch.
3. Persist `Role.SYSTEM_ADMIN.value` as the canonical role key. Make the zero-admin guard block both canonical rows and inert legacy display-label rows; do not convert legacy data or enable it.
4. Run the focused test, existing bootstrap/auth regression, full backend suite, scoped Ruff checks and `git diff --check`.
5. OpenCode independently reruns the assigned checks. A separate Hermes Reviewer reviews the scoped diff and evidence. Keep `CHPMIS-014` open until findings are resolved.

## Task 2 — CHPMIS-013 PostgreSQL schema, migration and CI contract

Update PostgreSQL expectations to actual head, add live empty and populated prior-schema upgrade assertions, inspect actual schema contract, fix formatter violations, supply only synthetic CI Compose inputs, and prove any downgrade limitation after bootstrap. Prefer forward migrations; do not rewrite applied migration history.

## Task 3 — CHPMIS-015 System Admin request transaction and concurrency

Make one service/application boundary own role changes, session revocation and request-decision writes. Revalidate active requester, approver and target authority at decision time. Use PostgreSQL-safe conditional transition/locking and fault-injection/concurrency tests; preserve approved dual-control policy.

## Task 4 — CHPMIS-016 bootstrap trust boundary

Use the reviewed fixed synthetic trust source only. Keep production nominations/custody unapproved and fail closed outside the explicitly supported local environment. Unit tests may use in-memory API fixtures but cannot be presented as host ACL or two-person proof. No real registry or host security mutation.

## Task 5 — CHPMIS-017 endpoint authorization matrix

Translate the approved role/scope contract into a table of HTTP endpoints × role × resource scope, then add positive and negative API integration tests. Ensure Auditor reads only its scoped audit trail, System Admin has no implicit business-data access, Member updates only their assigned task, department membership alone grants nothing, and multi-role users fail closed consistently.

## Task 6 — CHPMIS-012 browser OIDC and authenticated synthetic E2E

Connect Vite and backend API routing; configure a browser-facing issuer and container backchannel; bind expiring one-use state to initiating browser, use PKCE, enforce configured issuer/audience, and complete safe callback/login/logout/session-expiry/access-denied UX. Test state swap, nonce, replay, logout, CSRF and callback allowlist. Do not weaken Secure/CSRF/token checks.
Run Playwright on isolated loopback-only frontend/backend/PostgreSQL/Keycloak resources. Exercise login, project/member/task flow, dashboard, authorized audit, logout, and negative scope/CSRF/callback cases. Seed synthetic accounts through explicit test mechanisms; do not mock the business API or bypass OIDC. Preserve existing `chpmis010` state/volume. Both code repair and complete browser → backend → PostgreSQL → Keycloak journey stay under this one reserved task ID and its task pack must explicitly split/allowlist the necessary scoped phases.

## Tasks 8–9 — CHPMIS-018 consistency and CHPMIS-019 UI correctness

Use PostgreSQL competing writers for task transitions, test membership/manager consistency without inventing an unapproved minimum-manager rule, normalize structured API errors, prevent stale responses from updating a different project, clear data on expired sessions, and render due dates as calendar dates independent of host timezone.

## Closeout gates

- Exact baseline/final SHA, branch, status, changed-file allowlists, commands, exit codes, test counts and skips are recorded.
- No in-scope P1/P2 remains open; review is independent and accepted.
- Required PostgreSQL and authenticated synthetic E2E checks pass on the same final SHA; remote CI evidence is from that SHA.
- Only after those gates may the coordinator prepare the multi-department spec/plan; policy decisions about authority/official titles remain separate Human Gates.
- Production status remains NOT APPROVED.
