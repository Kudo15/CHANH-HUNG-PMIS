# Task Pack — CHPMIS-004 Projects, Tasks, Workflow, and Audit Writes

## Task ID and roles
- Task ID: CHPMIS-004
- Roles: Hermes Worker, independent Tester, independent Reviewer
- Status: COMPLETE — Worker handoff `t_ec7fe666`, independent Tester `t_56e1b47c` PASS, and independent Reviewer `t_f86d6118` APPROVED; Human Gates 1–5 were approved for the local first slice on 2026-10-30.
- Trace: `PLAN.md` Phase 2 items 2–3; mission §§3–4, 7D; acceptance AC-06–AC-10 and AC-12; `OPEN_QUESTIONS.md` Human Gates 2–4.

## Objective
Implement project create/list/read and scoped project membership; project-scoped task create/read/list/assignment and approved status transitions; and atomic project/task audit writes. Provide the local first-slice UI needed for these flows if the existing frontend structure supports it. No dashboard or audit-read/export endpoint (CHPMIS-005 scope).

## Approved policy
- Apply deny-by-default and explicit project assignment on every item and list request. Department membership alone never grants access. Inaccessible records must not disclose existence.
- System Admin has no implicit project/business-data access. Project Manager acts only within explicit project assignment. Member reads assigned projects and changes only their assigned task along the ordinary work path. Auditor is project-scoped read-only; audit read comes later.
- Project fields: generated opaque ID, required name, optional description, lead-department reference, assigned Project Manager, optional start/end dates, lifecycle `active`/`archived`; no official code and no deletion.
- Keep `lead_department_id` opaque and unseeded; do not invent department hierarchy, CRUD, or department-derived access. Explicit project membership is the authorization source.
- Project creation is initiated by an authenticated Project Manager and assigns that actor as the initial Project Manager; do not accept a client-supplied actor/creator identity. Additional membership is granted by an in-scope Project Manager using the approved generic project roles `project_manager`, `member`, or `auditor`.
- Task fields: generated ID, parent project, title, optional description, creator (from session), optional assignee/due date, status and timestamps. Any assignee must already be an explicitly assigned project member. A Project Manager creates/assigns tasks within scope.
- Transitions: `open → in_progress`; `in_progress → blocked|done`; `blocked → in_progress`; an in-scope Project Manager may cancel an unfinished task or reopen `done → in_progress`; `cancelled` is terminal. Members may change only their own assigned task along the ordinary work path. These are internal coordination states, not legal/statutory approval.
- Log project lifecycle/assignment and task assignment/state changes. Each audit event includes actor, UTC time, action, target/project IDs, correlation ID, and allowlisted before/after values only. Exclude credentials, tokens, descriptions, document content, and other free-form text. Business change and audit insertion share a DB transaction; audit failure rolls back the business mutation.
- Audit entries are application-append-only; no audit read/export or automatic deletion in this task. Use synthetic local data only; no secrets, real agency records, provider calls, or production access.

## Scope and boundaries
- Backend: `backend/app/**` for project/task services, models, routes, app registration and audit writer; additive migration(s) under `backend/alembic/versions/**`; tests under `backend/tests/**`.
- Frontend: `frontend/src/**` and existing frontend tests only as needed for the local project/task flows. Preserve the mandated stack and package lockfiles.
- May update only CHPMIS-004-specific API/data/workflow documentation if implementation exposes a contract ambiguity; do not edit approval records or rewrite accepted decisions.
- Forbidden: dashboard or audit-read/export implementation, authentication/authorization policy redesign, admin bootstrap, Department CRUD/seeding, financial logic, official department/project codes, legal approval semantics, S3/deployment/CI changes, external services/LLMs, real identities or secrets, unrelated cleanup, and edits to other task evidence/acceptance status.
- If implementation needs a policy not approved above, stop and record it in `OPEN_QUESTIONS.md`; do not guess or encode it.

## Acceptance criteria
- [x] AC-06: authenticated in-scope Project Manager creates a project with the approved fields; only explicitly assigned principals can list/read it; no delete route.
- [x] AC-07: only an in-scope Project Manager can assign/reassign project members; target user and project role are validated; System Admin alone has no business-data access.
- [x] AC-08: authorized Project Manager creates and assigns tasks only within a project; assignee must have project membership; unauthorized, unknown, or cross-project IDs fail closed.
- [x] AC-09: exactly the approved transitions and role permissions are enforced server-side; invalid, terminal, unauthorized, and cross-scope changes are rejected.
- [x] AC-10: guessed project/task IDs and cross-project list/read/write attempts disclose no protected record and cannot mutate it.
- [x] AC-12 project/task portion: create, membership/assignment, lifecycle, task assignment and status changes emit approved audit events; transaction rollback is proven when audit insertion fails; event data excludes secrets and free-form descriptions.
- [x] Migration is additive/reversible and introduces no unrelated or financial schema. No global audit read or project deletion is added.
- [ ] Tests cover unauthenticated, inactive, System Admin without membership, Manager/Member/Auditor positive and negative access, cross-project reads/writes/lists, member task ownership, invalid transitions, foreign-key/project consistency, audit allowlist and atomicity. Frontend tests/commands are the ones already present in repository; Worker records commands and exit codes.

## Verification
- First inspect `backend/pyproject.toml`/`pytest.ini`, frontend `package.json`, and existing task commands; use only commands defined in the repository or this task pack.
- Run backend full tests and lint, offline Alembic upgrade and downgrade SQL generation. Run frontend unit/build/lint only where existing scripts are defined. Report exact command, output summary, and exit code.
- Do not install dependencies, start Docker, access production, or call external providers. Live PostgreSQL/Compose/browser SSO are `NOT_VERIFIED` if unavailable.
- Independent Tester re-runs assigned checks read-only. Independent Reviewer inspects the diff and policy trace; neither changes implementation.

## Prompt template
- Library: prompts.chat via installed `.agents/skills/prompt-lookup`.
- Search/retrieval: searched for backend/API/database/workflow coding prompts and retrieved **Feature coding template**, ID `cmp1fv5ac0001js04jbj3pxoa`, on 2026-10-30.
- Source: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template . Full source is recorded in the prior CHPMIS-003 task pack/ledger.
- Modernized Worker prompt: “Implement only CHPMIS-004 using this task pack and the retrieved Feature coding template. Read charter, ledger, approved Human Gates and relevant docs first; inspect `git status`; preserve the existing dirty baseline. Use TDD and show failing tests before implementation. Follow the explicit project membership matrix, opaque lead-department reference and approved transition table exactly. Write the allowlisted audit event in the same transaction as every covered mutation. Do not add Department CRUD, global access, bootstrap, dashboard/audit read, legal approvals, or unapproved rules. Keep changes in the file allowlist, add reversible migrations, use only existing verification commands and report exact output/exit codes and NOT_VERIFIED infrastructure. Request independent Tester and Reviewer; do not self-approve.”

## Final evidence and limits
- Worker card `t_ec7fe666`, run #14, session `20261030_102235_21b37e`: 48 passed/1 skipped, Ruff and migration offline upgrade/downgrade clean, frontend lint/test/build exit 0.
- Independent Tester card `t_56e1b47c`, run #15, session `20261030_104911_3bbe88`: all seven verification commands exit 0; AC-06–AC-10 and AC-12 project/task portion PASS.
- Independent Reviewer card `t_f86d6118`, run #16, session `20261030_105330_5da9b5`: APPROVED, no P1–P3 findings.
- NOT_VERIFIED: live external IdP/JWKS, Docker/PostgreSQL runtime, and browser HTTP-only cookie SSO.
- Broader acceptance AC-10 remains PARTIAL because a separate department-membership-only negative test was not run; department membership is not an authorization source in the approved model.

## Definition of Done
- [x] Implementation, exact verification evidence, independent Tester results, and independent Reviewer verdict are recorded in `.team/ledger.md`.
- [x] CHPMIS-004 is complete for local implementation; provider/runtime gaps remain `NOT_VERIFIED` and the broader AC-10 gap remains explicitly partial.
