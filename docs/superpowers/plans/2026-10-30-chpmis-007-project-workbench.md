# CHPMIS-007 Project Workbench Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Execute this plan task by task, preserve the existing checkout, and follow the project task pack as the authoritative scope.

**Goal:** Replace the demo-like project panel with a responsive, usable Project Workbench backed only by the already-approved API and policies.

**Architecture:** Frontend-only React/TypeScript workbench. Keep the server authoritative for project membership, task assignment, transitions, and archive permission. Load the session, authorized projects, and only the selected project's members/tasks/dashboard/audit. Use in-memory CSRF from the session for existing mutations. Split UI components only where it improves the existing shell's maintainability.

**Tech Stack:** Existing React, TypeScript, Vite, Tailwind/UI primitives, Vitest and Playwright setup. No package or backend contract changes expected.

**Spec:** `docs/superpowers/specs/2026-10-30-project-workbench-design.md`

## Global Constraints

- Work only inside the CHPMIS-007 file allowlist in `.team/tasks/CHPMIS-007-project-workbench.md`.
- Preserve the pre-existing modified and untracked files. Do not reset, clean, stage, or commit.
- TDD: add/adjust focused tests first and observe a meaningful RED failure, implement the smallest scoped change, then run GREEN checks.
- Use existing API endpoints and response contracts only. No backend, schema, authentication, role, workflow, audit policy, or project membership changes.
- Do not add login shortcuts, localStorage session/CSRF storage, unauthorized cross-project fetches, or free-form assignee IDs.
- All API calls use same-origin cookie credentials; mutations send the in-memory CSRF token and rely on the server for authorization.
- Show IDs for project members and offer task assignees only from the selected project's existing member list.
- Do not claim live IdP, browser SSO, PostgreSQL runtime, or Docker evidence.

## Review Focus

1. A project not returned to the signed-in user is never fetched by guessing IDs; selected-project dependent requests run only after authorized project selection.
2. Project role is derived by matching session user ID to the selected project's member response; global role only gates project creation affordance.
3. CSRF remains in memory and mutation requests include `X-CSRF-Token`; failure responses do not disclose protected project data.
4. Task actions match the approved transition matrix and role/assignment checks; backend remains authoritative; archived projects are read-only.
5. Search/filtering is client-side on authorized loaded data, responsive/accessibly labeled, and errors/empty/loading/unauthenticated states remain understandable.

---

### Task 1: Implement and verify the Project Workbench

**Files:** `frontend/src/App.tsx`, `frontend/src/components/ProjectTaskManager.tsx` or a focused `frontend/src/components/ProjectWorkbench.tsx`, `frontend/src/App.test.tsx` or focused tests under `frontend/src/**`; styles only under `frontend/src/**` if needed.

**Interfaces:** Consume existing `/api/v1/auth/session`, `/api/v1/projects`, `/api/v1/projects/{id}`, `/api/v1/projects/{id}/members`, `/api/v1/projects/{id}/tasks`, `/api/v1/dashboard/summary`, `/api/v1/projects/{id}/audit-events`, `POST /api/v1/projects`, `POST /api/v1/projects/{id}/tasks`, `PATCH /api/v1/tasks/{id}/status`, and `POST /api/v1/projects/{id}/archive` contracts. Dashboard endpoint returns per-authorized-project items plus aggregate totals; display only the matching selected project's item and do not render cross-project totals. Confirm payload schemas in backend routes/schemas before wiring; do not alter them.

**Steps:**

- [ ] Add focused tests for shell/session states, authorized project selection and project-scoped load, task search/filter, project/task create mutation payloads, approved role/assignment transition affordances, archive confirmation/read-only state, and API/CSRF failures. Run the focused Vitest command and capture a meaningful RED result.
- [ ] Implement responsive project navigation/search and selected project overview with metadata, member IDs/roles, scoped dashboard, tasks, and audit history; include loading, empty, error, and unauthenticated states.
- [ ] Implement project creation for global Project Managers with existing fields and API only.
- [ ] Implement task creation/assignment for an in-scope Project Manager, with assignee choices constrained to selected-project members.
- [ ] Implement task status controls matching approved project role, assignment, task state, project lifecycle, and exact transition matrix; refresh affected project data after successful mutation.
- [ ] Implement confirmed archive action for in-scope Project Manager; archived project remains view-only.
- [ ] Run focused tests, then `npm --prefix frontend run test -- --run`, `npm --prefix frontend run lint`, and `npm --prefix frontend run build`; run `npm --prefix frontend run test:e2e` if its repository-defined setup can execute without external services. Report exact commands, outputs, and exit codes; mark unavailable checks NOT_VERIFIED.
- [ ] Report changed files, acceptance mapping, meaningful RED/GREEN evidence, exact verification commands/results, and any gaps. Do not update first-slice acceptance statuses.

