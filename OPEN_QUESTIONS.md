# Open Questions and Human Gates

Unanswered items below are blockers when they affect implementation. Use synthetic examples only; do not guess official process, role, legal, or financial rules.

## Approval record — 2026-10-30
- The project owner approved the complete recommendation package in chat for the **local first slice only**. This is internal project approval, not legal approval or production authorization.
- HG1–HG5 choices for that scope are recorded in the corresponding architecture/security/workflow documents and summarized below. CHPMIS-001 may unblock dependent local-first-slice work.
- Production identity-provider selection/configuration, official record-retention schedule, privacy/classification requirements, S3 provider, deployment, and production operations remain outside this approval and require their own evidence/approval.

## Human Gate 1 — Identity and account lifecycle — approved for local first slice
- Organization SSO via provider-neutral OIDC; no public self-registration and no local-password fallback. The exact agency IdP and its non-secret configuration remain to be supplied before connecting to a real provider.
- IdP is authoritative for identity/account state and department membership. PMIS controls explicit project membership separately.
- MFA is managed by the IdP; phishing-resistant authentication should be available. Sign-in is allowed only for an authorized organization identity.
- Use server-managed opaque sessions in Secure, HttpOnly, SameSite=Lax cookies with CSRF protection, rotation on authentication/privilege changes, and revocation on logout/deprovision. Proposed limits: 30-minute inactivity and 12-hour absolute lifetime.

## Human Gate 2 — Authorization and organizational scope — approved for local first slice
- Enforce least privilege and deny by default on every server request. Project scope is explicit project membership; department membership alone does not grant project access.
- Approved generic roles and actions: System Admin manages account/role configuration but has no implicit business-data access; Project Manager manages projects in scope, assigns project members and tasks, manages transitions, and archives; Member reads assigned projects and changes only own assigned task state; Auditor reads audit events only for projects explicitly in scope. No global auditor role in this slice.
- Role names are configurable policy keys, not official titles. No actual departments or official titles may be seeded.
- A user may not self-grant System Admin. Grant/revocation of System Admin requires a second existing System Admin. Cross-department cooperation requires explicit project membership.
- Still open for any usable installation: how the initial two System Admin identities are nominated and provisioned. Do not implement first-admin self-bootstrap or seed real identities; local authorization tests may use synthetic fixtures only.

## Human Gate 3 — Project and task model — approved for local first slice
- Project: generated opaque ID, required name, optional description, lead-department reference and assigned Project Manager; optional start/end dates; lifecycle `active`/`archived`. No official project-code scheme and no deletion are introduced.
- Task: title, optional description, creator, optional assignee, optional due date, status, timestamps; assignment/reassignment is by an in-scope Project Manager to a project member.
- States: `open → in_progress`; `in_progress → blocked|done`; `blocked → in_progress`; Project Manager may cancel an unfinished task or reopen `done → in_progress`; `cancelled` is terminal. Members may transition only their assigned task along the ordinary work path. No legal/statutory approval semantics are represented.
- Dashboard: counts by task state and overdue tasks for projects the caller may access; no financial metrics or personnel ranking.

## Human Gate 4 — Audit and privacy — approved for local first slice
- Record authentication events, role grants/revocations, project lifecycle/assignment changes, task assignment and state changes. Capture actor, UTC time, action, target/project IDs, correlation ID, and allowlisted before/after values. Exclude credentials, tokens, document contents, and free-form descriptions.
- Audit reads are project-scoped; no global audit access or export in this slice. Audit records are append-only at the application level.
- Audit write and business mutation share a transaction. On audit-write failure, roll back the mutation and return an error.
- Synthetic local development data only; no automatic audit deletion in this local slice. Production remains blocked until an authoritative records-retention and privacy/classification schedule is verified. No real documents are in scope.

## Human Gate 5 — Platform and operations — approved for local first slice
- Keep the mandated stack and existing dependency lockfiles. Use the repository's existing GitHub Actions CI workflow for checks only; no deployment job.
- Run with the existing Docker Compose/PostgreSQL local setup and bind published development services only to `127.0.0.1`.
- Defer S3 provider, deployment environment, production performance/availability/backup targets, and operational SLAs until a separately approved hosted environment and requirements exist.

## Legal / finance gates
- Which official sources and verifier/approver will govern procurement, contract, construction, records, privacy, finance, disbursement, acceptance, and settlement requirements?
- What is the authorized source of official financial values and who may approve any future calculations?
- No legal rule or financial policy is currently verified; see `docs/legal/LEGAL_RULES_REGISTER.md`.

## Tooling status — checked 2026-10-30
- Prompt lookup is installed and verified: the CHPMIS-001 Security Reviewer prompt was searched and retrieved from prompts.chat (Vulnerability Auditor Agent Role, ID `cmmx31zon000dk604l79f55ac`).
- Hermes CLI Kanban is operational for explicit dispatch: card `t_6dd0b4b2` completed on the `default` profile. Gateway remains stopped; use explicit dispatch for future cards. Model/provider/effort were not exposed in that run.

## Current handoff — CHPMIS-011 (2026-10-31)
- Active routing: Hermes Worker/Reviewer, independent OpenCode Tester, Codex Coordinator/Planner; inherit configured defaults and dispatch sequentially while baseline is uncommitted. Exact model IDs are reported only when surfaced by a run.
- AC-10 is PASS after CHPMIS-008. AC-01/03 are PASS after actual CHPMIS-010 runtime evidence and Hermes independent evidence review. Remaining NOT_VERIFIED: AC-04 (remote CI), AC-05/14 (actual IdP/browser journey).
- CHPMIS-010 completed the scoped test correction and live initially empty PostgreSQL migration verification: head 0004_projects_tasks_audit, exact ten tables, focused 1 passed/full 63 passed. Owner approved CHPMIS-011's local synthetic Keycloak and one-time two-person bootstrap design on 2026-10-31. OpenCode T1 ran the six assigned checks (97 passed/1 skipped) and read the tests after owner-authorized verifier shell setup; its separate scoped Git status remains denied despite an exact allow rule. Hermes R2 reports APPROVED with a scope-evidence limitation; isolated live runtime remains. See `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `.team/tasks/CHPMIS-011-T1-test-evidence.md`, and `docs/superpowers/plans/2026-10-31-chpmis-011-local-oidc-bootstrap.md`.
- A prepared CHPMIS-009 candidate manifest is not a commit. Worktree readiness requires a separately created and verified local commit containing the source baseline.
- Actual agency IdP, official approver/key nomination and custody, real identities, production grants, and remote/push remain unapproved; existing HG1–HG5 local decisions are unchanged.

## CHPMIS-011 Human Gate — local design approved; later gates remain, 2026-10-31
Owner explicitly approved the complete local synthetic design and directed immediate execution. See `docs/superpowers/specs/2026-10-31-chpmis-011-local-oidc-bootstrap-design.md` and its bounded implementation plan. The approved local slice includes loopback Keycloak, internal backchannel, synthetic test identities, the Project Owner + distinct Security Reviewer two-person roles, offline signed approvals, append-only receipt/migration, and a one-time CLI. Actual provider selection/connection, official approver authority and key custody, real identities, production grants, and deployment remain later Human Gates. Do not store real identifiers or credentials in Git/chat.

## CHPMIS-011 follow-up proposal — UNAPPROVED, local synthetic only

**Owner decision, 2026-10-31:** Owner explicitly selected “Duyệt đề xuất local (khuyến nghị)” in response to the proposal below: preconfigured synthetic trusted keys, instance-bound signatures with maximum validity of 24 hours, synthetic operator identifier and database receipt protection. This approves those local synthetic policy/schema changes only. The implementation-level details still require an explicit bounded design/plan and independent review; real authority, real identities, production and actual key custody are not approved. The text below records the proposal as it was presented; the heading is retained as historical context, superseded by this decision.

R3 reviewer `t_650be3b1` identified gaps between the approved design and the present implementation: caller-supplied approver keys do not establish trusted role identity or two distinct people; signed payloads lack freshness/instance binding; receipts lack an operator field and database-enforced immutability. The local synthetic tests cannot establish real human independence. Actual organizational identity and custody decisions remain a separate later gate.

**Concrete proposal for an owner decision, not an implemented policy:**

1. Provision two distinct synthetic public keys for the two approved roles separately from each bootstrap invocation, through a local protected configuration established before approvals are signed. Remove caller-selected keys from the normal bootstrap invocation; reject missing/untrusted/identical keys. A protected configuration is a trust assumption: whoever can replace it can redefine the local trust anchor, and two keys alone cannot prove two humans.
2. Bind each approval to the environment, a persistent randomly generated local test-instance identifier, ordered target subjects, a unique approval request ID, issuance time and expiration time. For the synthetic exercise propose a **24-hour maximum validity**, reject expired, not-yet-valid, mismatched and reused approvals. This number is a proposed local test rule, not an official deadline or legal requirement.
3. Add an opaque synthetic operator identifier and approver-key fingerprints to the receipt; keep receipt and both grants transactional. Enforce update/delete rejection for receipts in the local database, and document its boundary: database owners or privileged administrators may be able to alter or bypass controls. No real names, secrets or signatures in source or the receipt.
4. Add focused tests for untrusted keys, same key, expiry, instance/payload mismatch, replay, receipt alteration and transaction rollback; obtain fresh independent review. No real identities or production authorization are implied.

Approval is required before changing authorization semantics, freshness window or schema. A chosen protected-key custody mechanism, the precise operator attribution mechanism and database role/privilege setup must be specified and reviewed before implementation; record any further unresolved choice rather than claiming these controls already exist. Owner may approve or modify this local-only proposal after reviewing it.

### Current follow-up status after owner approval

- The owner's approval above covers the local synthetic policy objectives. The implementation follow-up W9 is **BLOCKED** before product edits: the prescribed fixed trust store's effective Windows ACL and every ancestor's replacement/reparse boundary have not been demonstrated safely under the current unprivileged/no-host-change constraints. Prototype `t_0ae2472c` used Windows APIs on in-memory descriptors, but Coordinator observed token-dependent results and no real two-account or ancestor-race proof. Do not treat an in-memory example as proof of the real host boundary.
- Next technical work: produce and independently review a handle-based, race-resistant trust-source design and a concrete local provisioning/integration procedure. Any proposal to create or modify real local accounts, ACLs or protected files must identify the exact changes and request separately appropriate authorization before applying them. No private key or real user identity is to be posted in Git/chat. Until the security and runtime gates are satisfied, the W8 runbook remains **DO NOT EXECUTE**, and AC-05 live evidence remains NOT_VERIFIED.
- W10 test-only correction is independently tested/reviewed: an injected failure after receipt flush rolls back on the SQLite in-memory test path. OpenCode's full backend suite passed 98 with 1 skipped. This does not prove PostgreSQL behavior or close W9. The OpenCode scoped Git status denial remains unresolved.

### CHPMIS-016 owner policy question — shared HKLM root SID — RESOLVED 2026-11-01

- Owner decision: check effective rights only at `HKLM\\SOFTWARE`; keys created by CHPMIS must be owned by `BUILTIN\\Administrators` (`S-1-5-32-544`).
- F2 must not enforce an owner allowlist or the task-key SDDL on the shared root. This resolves application policy only; current Windows host Registry state was not inspected and no Registry call was executed.

### CHPMIS-017 multi-role authorization combination — RESOLVED 2026-11-01

- Owner selected permission intersection across all applicable roles: an action is allowed only if every role permits it. Project-scoped actions additionally require explicit project assignment and permission from the `ProjectMember.role`; task-specific scope and transition constraints still apply.
- System Admin + any business role therefore has no business-data access. No union or role-precedence shortcut is allowed.
- This decision resolves the local application policy for CHPMIS-017 only; it is not legal approval or production authorization.

### CHPMIS-017 repository-wide Ruff findings — RESOLVED (2026-11-01)

- The corrected read-only OpenCode verifier ran both pytest suites, Ruff format, and `git diff --check` successfully, but repository-wide Ruff reported 19 import-order (`I001`) errors.
- Five errors are inside CHPMIS-017's approved test-file allowlist. Fourteen are in other files in the existing dirty workspace, including Alembic revisions and test modules outside CHPMIS-017's allowlist; editing those files would exceed the CHPMIS-017 task pack.
- Owner selected to keep the CHPMIS-017 allowlist, fix only the five I001 findings in four allowed test files, accept Ruff scoped to the seven CHPMIS-017 files, and track the other 14 findings separately. This revises CHPMIS-017's lint criterion only; the repository-wide lint failure remains recorded, not passed.
- The 14 findings remain open for separately scoped tasks. No changes outside the CHPMIS-017 allowlist are authorized by this decision.
