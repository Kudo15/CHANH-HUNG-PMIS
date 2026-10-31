# Task Pack — CHPMIS-005 Scoped Dashboard and Audit History

## Task ID and roles
- Task ID: CHPMIS-005
- Roles: Hermes Worker, independent Tester, independent security-focused Reviewer.
- Status: COMPLETE — Worker handoff `t_0c1b86d4`, Tester `t_4a4fb440` PASS, and security-focused Reviewer `t_2cfd81ae` APPROVED.
- Trace: `PLAN.md` Phase 2 item 4 and Phase 3; mission §§3–4, 7D–8; acceptance AC-11–AC-13; `OPEN_QUESTIONS.md` HG2–HG4.

## Objective
Implement a minimal project-scoped dashboard summary and project audit-history read API/UI using the CHPMIS-004 project/task and audit records. Protect aggregate and audit reads using the approved membership/reader policy. No global audit access, export, audit mutation, retention purge, or financial metrics.

## Approved policy and exact slice
- Enforce authenticated active session, deny-by-default, and explicit project membership server-side. Department membership alone grants no project access. System Admin has no implicit business-data access.
- Dashboard may show counts of tasks by approved status and count of overdue tasks, limited to projects explicitly available to that caller. No financial metrics, personnel rankings, or aggregate from unauthorized records. Each returned project/count is derived only after project membership scope is applied.
- For this local slice, treat an overdue task as one with a non-null due date earlier than the current UTC instant and status other than terminal `done` or `cancelled`. Keep this definition centralized, deterministic in tests with frozen time, and label it plainly in the UI.
- Audit history is scoped to one explicitly assigned project. As specified in the approved API contract, allow an in-scope Project Manager or Auditor; Member, System Admin without membership, unauthenticated, inactive, guessed, and cross-project access must fail closed without record disclosure. If the implementation or accepted role docs appear to conflict on reader role, do not broaden access; record the exact ambiguity in `OPEN_QUESTIONS.md` and block the affected endpoint for human resolution.
- Return only existing audit metadata and allowlisted before/after values: actor ID, UTC timestamp, action, target/project IDs, correlation ID, and safe values. Do not expose descriptions, names/titles, credentials/tokens, document content, or arbitrary JSON fields. Audit remains application-append-only; this task adds read-only endpoints only.
- No global audit endpoint, export/download, audit edit/delete, automatic retention, or schema redesign.
- For audit lists, use stable newest-first ordering and server-side bounded cursor pagination; cap page size at 100 and return an opaque cursor/has-more indicator. Do not infer an official retention or completeness boundary.
- Synthetic local data only. No real IdP, external services/LLMs, Docker/PostgreSQL startup, production access, or secrets.

## Scope and boundaries
- Backend: dashboard/audit read services and routes under `backend/app/**`, app registration only if needed, tests under `backend/tests/**`.
- Frontend: `frontend/src/**` and existing UI tests only for scoped summary/audit views.
- API documentation may be updated only to document the exact local contract above.
- No migration is expected; if the Worker finds a required schema/data-retention/auth policy change, stop and open a scoped proposal rather than modifying schema or inventing policy.
- Forbidden: product-code changes outside dashboard/audit reads, changing CHPMIS-004 audit writes or auth matrix, global aggregates/audit reads, exports, deletion/purge, Department CRUD, admin bootstrap, finance/legal semantics, real providers, deployment/CI, unrelated cleanup, or changing prior acceptance evidence.
- AC-14 end-to-end sign-in path remains `NOT_VERIFIED` while the actual IdP is unselected; do not add a fake login or weaken authentication to make the flow pass.

## Acceptance criteria
- [x] AC-11: authenticated user sees project/task status counts and overdue task counts only for explicitly assigned projects; no unauthorized project contributes to a list, count, or aggregate.
- [x] AC-12 read portion: project/task audit events are retrievable with only approved metadata/allowlisted values; read path is read-only and preserves existing append-only records.
- [x] AC-13: only an explicitly assigned Project Manager or Auditor can read that project's audit events; Member, unrelated System Admin, unauthenticated/inactive principal, guessed project ID, and cross-project request fail closed without disclosure.
- [x] Cursor pagination is stable/newest-first, bounded, and cannot cross project scope.
- [x] UI clearly associates dashboard counts and audit history with the authorized project, without rendering free-form or excluded audit content.
- [x] Tests cover mixed authorized/unauthorized project fixtures, all task status counts, overdue boundaries and terminal exclusion, reader-role matrix, guessed/cross-scope IDs, cursor tampering/reuse, safe field allowlist, and no mutation through read routes.
- [x] Worker, Tester and security-focused Reviewer recorded exact evidence. Real IdP/browser SSO and live PostgreSQL/Compose remain `NOT_VERIFIED`.

## Verification
First inspect backend/frontend package scripts and project test configuration. Run only commands already present in the repository/task pack: backend full pytest, Ruff, Alembic offline upgrade/downgrade SQL; frontend unit, lint, build and any existing scoped E2E script. Report exact commands, output summary and exit codes. Do not install dependencies or start services. Tester independently reruns the listed verification read-only.

## Prompt template
- Source: prompts.chat **Feature coding template**, ID `cmp1fv5ac0001js04jbj3pxoa`, found through installed `.agents/skills/prompt-lookup` search for “Feature coding template” and retrieved previously on 2026-10-30: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Modernized Worker prompt: “Implement only CHPMIS-005 using this task pack and the retrieved Feature coding template. Read charter, ledger, accepted Human Gates and CHPMIS-004 contract first; inspect and preserve `git status`. Apply server-side project membership before every aggregate or audit query. Use only the explicitly approved dashboard metrics and audit reader roles. Keep audit response fields strictly allowlisted, read-only, bounded and cursor-paginated. Do not add a fake login, migration, export, global audit access, retention behavior, Department CRUD, finance/legal rules or unrelated cleanup. Use synthetic fixtures; use TDD and existing repository verification commands; record exact commands/output/exit codes and all `NOT_VERIFIED` limits. Request independent Tester and security-focused Reviewer; do not self-approve.”
- Tester source: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, previously retrieved and modernized in CHPMIS-004-T1; adapt read-only and do not create template TODO files.
- Reviewer source: prompts.chat **Senior Code Reviewer (severity-ranked)**, ID `cmv9n79m30005ku060pzornri`, previously retrieved and modernized in CHPMIS-004-R1; include aggregate isolation and audit reader/field integrity security checks.

## Definition of Done
- Implementation and exact Worker verification evidence recorded.
- Independent Tester reports exact commands/results and AC-11–AC-13 trace without file edits.
- Independent Reviewer returns `APPROVED` or `CHANGES_REQUESTED` with severity-ranked file:line findings.
- AC-11–AC-13 statuses reflect evidence; real IdP, live DB/container/browser gaps remain `NOT_VERIFIED`.

## Worker handoff
- Card `t_0c1b86d4`, run #17, session `20261030_105924_4702ff`; implementation handoff complete, acceptance pending independent roles.
- Backend: `.venv/Scripts/python -m pytest -v` — 61 passed, 1 skipped; Ruff exit 0; Alembic offline upgrade/downgrade SQL exit 0.
- Frontend: lint, Vitest (6 passed), build exit 0.
- NOT_VERIFIED: actual IdP/browser SSO; Docker/PostgreSQL runtime.

## Independent role task packs
- Tester: `.team/tasks/CHPMIS-005-T1-test-evidence.md`.
- Reviewer: `.team/tasks/CHPMIS-005-R1-security-review.md`.

## Final independent evidence
- Tester card `t_4a4fb440`, run #19, session `20261030_113154_4afe39`: seven commands exit 0; 61 backend tests passed, 1 PostgreSQL integration skipped; 6 frontend tests passed; AC-11–AC-13 PASS; no files modified.
- Security Reviewer card `t_2cfd81ae`, run #20, session `20261030_113604_937223`: `APPROVED`, no P1/P2/P3 findings, no file changes.
- NOT_VERIFIED: actual IdP/JWKS/browser SSO; Docker Compose and live PostgreSQL runtime.


## Hermes Worker card contract

ROLE: worker (implementation)
Work only inside this task's workspace.
1. Read the task pack, charter, ledger, approved Human Gates, and existing CHPMIS-004 contracts before editing.
2. Use TDD; inspect and preserve the existing dirty baseline. Implement the smallest scoped change.
3. Run the existing repository checks listed in the task pack and report exact commands/output/exit codes plus NOT_VERIFIED limits.
4. Post progress with kanban_comment.
Finish with exactly one of:
- kanban_complete(result=what changed, how verified, and what remains)
- kanban_request_review(summary=implementation handoff and evidence)
- kanban_block(reason=exact unresolved requirement or policy gap)

--- REQUIREMENT ---
Implement only `.team/tasks/CHPMIS-005-dashboard-audit-read.md` using its real Feature coding template reference. Keep dashboard counts/overdue and audit reads strictly scoped to explicit project membership. Preserve CHPMIS-004 write behavior. No fake auth, global audit, export, migration, data retention, or production work. If any policy conflicts or unapproved scope is necessary, stop and record the gap.
