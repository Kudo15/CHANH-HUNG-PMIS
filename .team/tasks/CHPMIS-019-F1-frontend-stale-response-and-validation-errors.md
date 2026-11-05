# CHPMIS-019-F1 — Safe API Errors and Project-Scoped Async Results

## Task identity

- **Task ID:** CHPMIS-019-F1
- **Role:** Hermes Frontend Worker; then OpenCode read-only Tester and separate Hermes Reviewer
- **Status:** COMPLETE — Worker implementation and independent review are recorded. OpenCode passed focused/full frontend tests, lint and build; its scoped `git diff --check` was denied, and the owner explicitly accepted the Coordinator's exact scoped check and existing independent review for that one command. Fresh CHPMIS-022 OpenCode Reviewer approved the narrow test evidence after reading the required session documents. The original verifier's missing session-start reads remain a recorded process gap, not a retroactive pass. Details: `.team/tasks/CHPMIS-019-F1-opencode-readonly-verification.md`.
- **Trace:** mission §6, CHPMIS-019 UI reliability; existing frontend project-workbench contract.

## Objective

Prevent React from receiving non-string API error details and ensure asynchronous project refreshes only update the project whose view is still selected.

## Coordinator approach

Follow the existing React/Vitest stack. Add one small shared formatter for FastAPI error details and guard project-scoped refresh/pagination state writes against a selection change. Keep the current selection effect's cleanup guard. Do not refactor the UI or introduce a data-fetching framework.

## Scope

Allowed product files:

- `frontend/src/components/ProjectWorkbench.tsx`
- `frontend/src/ProjectWorkbench.test.tsx`
- `frontend/src/lib/apiError.ts` (new, if a shared formatter is used)
- `frontend/src/lib/apiError.test.ts` (new, if the formatter is tested separately)

Append only `.team/tasks/CHPMIS-019-F1-worker-report.md`.

Do not change backend APIs, authorization policy, logout/session-expiry semantics, date/timezone interpretation, PM transfer/last-manager behavior, workflow transitions, or other components. Do not add dependencies or refactor the full workbench.

## Required RED/GREEN behavior

1. A FastAPI 422 whose `detail` is an array of validation objects renders a useful string and does not crash React. An object-shaped detail is handled safely too. Only display trusted error-message/location fields; never stringify or expose submitted `input` values. Unknown or malformed shapes use the existing Vietnamese fallback message.
2. Start a project A mutation refresh, switch to project B, resolve B's detail requests, then resolve A's late response. The rendered members/tasks/dashboard/audit remain scoped to B.
3. A late audit-pagination response for A must not append rows or replace the cursor while B is selected, if that path can update shared component state.
4. Preserve existing project selection, initial load, CSRF, and request contracts.

Write the regression tests first and run them to confirm RED before changing product code. Use deferred promises in Vitest for the race; no timer-only race. Do not test or change 401/403/logout behavior in this task because that UX is recorded as an unapproved open question.

## Verification

From repository root:

- `npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx`
- `npm --prefix frontend run test -- --run`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`
- `git diff --check -- frontend/src/components/ProjectWorkbench.tsx frontend/src/ProjectWorkbench.test.tsx frontend/src/lib/apiError.ts frontend/src/lib/apiError.test.ts .team/tasks/CHPMIS-019-F1-worker-report.md`

Report each exact result and exit code. Do not commit. OpenCode verification is read-only and must use the configured default model with no override. Request independent review after the Tester result; if OpenCode is blocked, record NOT_VERIFIED and do not bypass its permissions.

## Prompt template

- Real template retrieved through the installed prompt-lookup workflow: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as the CHPMIS-019-F1 frontend Worker. First add focused Vitest regressions for array/object API validation errors and a deferred project A response arriving after selection changes to B; run them RED before product edits. Make the smallest change in the allowlisted files: normalize untrusted error detail into safe display text without echoing input values, and prevent late project-scoped refresh/pagination responses from writing into a different selected project. Preserve existing auth, CSRF, project selection, and UI contracts. Do not touch unresolved 401/403/logout, PM membership, workflow, or due-date semantics. Run the exact frontend checks, report outputs/exits, and request read-only Tester then independent Reviewer assessment; do not commit.”

## Definition of Done

- Both regression behaviors are covered and pass.
- Full frontend tests, lint, and build pass; diff check is clean.
- No files outside the allowlist changed for this Worker task.
- OpenCode result and independent review are recorded; unresolved auth/date/PM policies remain unimplemented.

## Hermes card closing contract

ROLE: worker (frontend). Work only in this task's workspace. Keep Worker, Tester, Reviewer serialized. Finish with exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include changed files, RED/GREEN results, exact commands/results/exits, requirement trace, Tester status, and remaining limits. Do not commit.
