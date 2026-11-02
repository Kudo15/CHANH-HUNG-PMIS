# CHPMIS-019-F1 Worker Implementation Report

- **Task ID:** CHPMIS-019-F1 (Kanban task `t_930129a8`)
- **Role:** Hermes Frontend Worker (implementation)
- **Status:** IMPLEMENTATION COMPLETE / READY FOR INDEPENDENT VERIFICATION & REVIEW
- **Requirement Traceability:** mission §6, CHPMIS-019 UI reliability; existing frontend project-workbench contract; `.team/tasks/CHPMIS-019-F1-frontend-stale-response-and-validation-errors.md`.
- **Prompt Template Trace:**
  - Real template: prompts.chat **Feature coding template**, author Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
  - Modernized task-specific Worker prompt: "Act as the CHPMIS-019-F1 frontend Worker. First add focused Vitest regressions for array/object API validation errors and a deferred project A response arriving after selection changes to B; run them RED before product edits. Make the smallest change in the allowlisted files: normalize untrusted error detail into safe display text without echoing input values, and prevent late project-scoped refresh/pagination responses from writing into a different selected project. Preserve existing auth, CSRF, project selection, and UI contracts. Do not touch unresolved 401/403/logout, PM membership, workflow, or due-date semantics. Run the exact frontend checks, report outputs/exits, and request read-only Tester then independent Reviewer assessment; do not commit."

---

## 1. Scope and File Compliance

Worker modified only allowlisted product and test files:
1. `frontend/src/lib/apiError.ts` (new):
   - Created safe API error formatting utility `formatApiError(detail: unknown, fallbackMessage: string): string`.
   - Handles FastAPI/Pydantic 422 error details (arrays of validation error objects, single error objects, or string details).
   - Only displays trusted message (`msg` / `message`) and location (`loc`) fields; never exposes or stringifies submitted untrusted `input` values.
   - Falls back safely to Vietnamese fallback messages for unknown, malformed, or empty shapes.
2. `frontend/src/lib/apiError.test.ts` (new):
   - Unit tests covering string inputs, null/undefined/primitive inputs, arrays of validation error objects, single error objects, `message` property fallback, nested `{ detail: ... }` unwrapping, malformed shapes, and exclusion of sensitive `input` fields (7 tests, all passing).
3. `frontend/src/components/ProjectWorkbench.tsx`:
   - Added `selectedProjectIdRef` (updated via `useEffect`) to track the currently selected project identifier across asynchronous gaps.
   - Guarded `refreshProjectData(projectId)`: checks `selectedProjectIdRef.current === projectId` after `Promise.all` resolves and inside each state updater and catch block. If the user has navigated away to project B, late responses from project A are safely discarded without overwriting members, tasks, dashboard summary, or audit events.
   - Guarded `handleLoadMoreAudit`: captures `currentProject = selectedProjectId` and checks `selectedProjectIdRef.current === currentProject` upon fetch completion before appending rows or updating `nextCursor` / `hasMoreAudit`.
   - Updated mutation handlers (`handleCreateProject`, `handleCreateTask`, `handleTransitionTask`, `handleArchiveProject`) to use `formatApiError(err?.detail ?? err, fallback)` instead of directly binding non-string objects to `actionError`.
   - Captured `currentProjectId = selectedProjectId` in mutation handlers to ensure `refreshProjectData(currentProjectId)` refreshes the project where the mutation originated without leaking across selection changes.
4. `frontend/src/ProjectWorkbench.test.tsx`:
   - Added comprehensive regression tests in describe block `CHPMIS-019-F1 safe validation errors and stale project responses`:
     - `safely handles FastAPI 422 array of validation objects without crashing React or leaking input`
     - `safely handles FastAPI 422 object-shaped detail and falls back for malformed shapes`
     - `ensures project A mutation refresh does not overwrite selected project B when A resolves late` (using Vitest deferred promises)
     - `ensures late audit pagination response for project A does not append to or overwrite selected project B` (using Vitest deferred promises)
5. `.team/tasks/CHPMIS-019-F1-worker-report.md`:
   - Authored this implementation report.

No files outside the allowlist were created or modified. No backend APIs, authentication/authorization policy, logout/session-expiry semantics, date/timezone interpretation, PM transfer/last-manager behavior, or workflow transitions were touched. No external dependencies were added.

---

## 2. Root Cause Analysis and Remediation

### Defect 1: FastAPI 422 Non-String Error Detail Crashing React
- **Root Cause:** FastAPI validation errors return `{ "detail": [ { "loc": ["body", "title"], "msg": "...", "input": "..." } ] }` or `{ "detail": { ... } }`. `ProjectWorkbench.tsx` previously did `setActionError(errorData?.detail ?? '...')`, assigning a raw array or plain object to `actionError`. When React rendered `{actionError && <div>{actionError}</div>}`, React threw an unhandled runtime error: `Objects are not valid as a React child (found: object with keys {loc, msg, type, input}).`
- **Remediation:** `formatApiError` extracts trusted `loc` and `msg` properties, sanitizes location (omitting redundant `'body'` prefix), formats as `${locStr}: ${msg}`, strictly excludes `input` fields, and defaults unknown/malformed shapes to the Vietnamese fallback string.

### Defect 2: Asynchronous Mutation Refresh Overwriting Selected Project
- **Root Cause:** When a task was created or transitioned in project A, `refreshProjectData(selectedProjectId)` was invoked. While its network requests (`/api/v1/projects/proj-001/members`, tasks, etc.) were in flight, switching to project B loaded project B's details. When project A's late response arrived, `refreshProjectData` called `setMembers`, `setTasks`, and `setAuditEvents` unconditionally, overwriting project B's view with project A's stale data.
- **Remediation:** Added `selectedProjectIdRef` tracking `selectedProjectId`. `refreshProjectData` verifies `selectedProjectIdRef.current === projectId` before any state write and in catch handlers.

### Defect 3: Late Audit Pagination Response Appending Across Projects
- **Root Cause:** `handleLoadMoreAudit` fetched cursor-based audit events for the active project. If the user changed project selection to project B before the response returned, `setAuditEvents((prev) => [...prev, ...auditData.items])` appended project A's older audit rows into project B's audit stream and updated project B's cursor to project A's cursor.
- **Remediation:** `handleLoadMoreAudit` captures the initiating project ID and discards the response if `selectedProjectIdRef.current !== currentProject`.

---

## 3. TDD RED/GREEN Evidence

### RED Verification (Before Implementation)
Executed `npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx` against the initial unpatched code with the new regression tests:
```
 RUN  v5.0.5 D:/ANH VU/Google Drive/VUHOCAI/Project/CHANH HUNG PMIS/frontend

 ❯ src/ProjectWorkbench.test.tsx (13 tests | 4 failed) 3328ms
   ❯ CHPMIS-007 Project Workbench (13)
     ❯ CHPMIS-019-F1 safe validation errors and stale project responses (4)
       × safely handles FastAPI 422 array of validation objects without crashing React or leaking input 1099ms
       × safely handles FastAPI 422 object-shaped detail and falls back for malformed shapes 1088ms
       × ensures project A mutation refresh does not overwrite selected project B when A resolves late 155ms
       × ensures late audit pagination response for project A does not append to or overwrite selected project B 91ms

⎯⎯⎯⎯⎯⎯ Uncaught Exception ⎯⎯⎯⎯⎯
Error: Objects are not valid as a React child (found: object with keys {loc, msg, type, input}). If you meant to render a collection of children, use an array instead.

⎯⎯⎯⎯⎯ Uncaught Exception ⎯⎯⎯⎯⎯
Error: Objects are not valid as a React child (found: object with keys {loc, msg, input}). If you meant to render a collection of children, use an array instead.

FAIL src/ProjectWorkbench.test.tsx > ensures project A mutation refresh does not overwrite selected project B when A resolves late
AssertionError: expected <p>Khảo sát địa chất tuyến cống</p> to be null
- Expected: null
+ Received: <p ...>Khảo sát địa chất tuyến cống</p>

FAIL src/ProjectWorkbench.test.tsx > ensures late audit pagination response for project A does not append to or overwrite selected project B
AssertionError: expected <div class="sm:col-span-2">...</div> to be null
- Expected: null
+ Received: <div ...>corr-p1-page2-late</div>

Test Files  1 failed (1)
Tests       4 failed | 9 passed (13)
Errors      2 errors
Exit code: 1
```

### GREEN Verification (After Implementation)
1. Focused Workbench Test Suite:
```
Command: npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx
Result: Test Files 1 passed (1), Tests 13 passed (13)
Exit code: 0
```
2. Formatter Unit Tests:
```
Command: npm --prefix frontend run test -- --run src/lib/apiError.test.ts
Result: Test Files 1 passed (1), Tests 7 passed (7)
Exit code: 0
```
3. Full Frontend Test Suite:
```
Command: npm --prefix frontend run test -- --run
Result: Test Files 3 passed (3), Tests 26 passed (26)
Exit code: 0
```

---

## 4. Verification Commands and Exit Codes

All 5 required verification commands were executed from repository root and passed with exit code 0:

1. `npm --prefix frontend run test -- --run src/ProjectWorkbench.test.tsx`
   - Exit code: `0`
   - Output: `Test Files  1 passed (1); Tests  13 passed (13); Duration 16.91s`
2. `npm --prefix frontend run test -- --run`
   - Exit code: `0`
   - Output: `Test Files  3 passed (3); Tests  26 passed (26); Duration 17.59s`
3. `npm --prefix frontend run lint`
   - Exit code: `0`
   - Output: `> chanh-hung-pmis-web@0.0.0 lint > eslint .` (0 errors, 0 warnings)
4. `npm --prefix frontend run build`
   - Exit code: `0`
   - Output: `tsc -b && vite build` (✓ built in 6.59s)
5. `git diff --check -- frontend/src/components/ProjectWorkbench.tsx frontend/src/ProjectWorkbench.test.tsx frontend/src/lib/apiError.ts frontend/src/lib/apiError.test.ts .team/tasks/CHPMIS-019-F1-worker-report.md`
   - Exit code: `0`
   - Output: Clean (0 whitespace/formatting errors)

---

## 5. Scope and Boundaries Compliance Declaration

- Backend APIs and routes: UNCHANGED (no backend edits).
- Authorization policies and global roles: UNCHANGED.
- Authentication/Session-expiry/401/403 UX: UNCHANGED (no unapproved UX modifications).
- Workflow status transitions and due-date logic: UNCHANGED.
- External dependencies: ZERO added (clean standard React/TypeScript).
- Git repository state: NOT staged, NOT committed. Ready for read-only Tester verification and independent Reviewer review.
