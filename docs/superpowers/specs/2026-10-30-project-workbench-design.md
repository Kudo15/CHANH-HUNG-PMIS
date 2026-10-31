# CHPMIS-007 Project Workbench Design

## Intent

Replace the current demo-like single-page project panel with a practical project workspace for authorized staff. A user should be able to find a project they can access, understand its current state and membership, and carry out the already-approved project and task actions from one clear screen.

## Goals

- Present an accessible, responsive application shell with the current signed-in user and clear loading, empty, error, and unauthenticated states.
- Let a Project Manager create a project using the existing project fields and API.
- Let a user search their authorized project list and inspect the selected project's approved metadata, existing members, scoped task summary, tasks, and project audit history.
- Let an in-scope Project Manager create a task and assign it only to a member already listed for that project.
- Let users perform only task transitions allowed by the already-approved project role and task assignment; the backend remains authoritative.
- Let an in-scope Project Manager archive an active project using the existing archive action, with a confirmation step; archived projects stay read-only.
- Add focused frontend tests for rendered state, local task filters, and successful/denied mutation flows.

## Non-goals and anti-goals

- No backend/API, database/schema, authentication policy, role matrix, or workflow transition changes.
- No new staff directory or UI for adding/changing project membership; the current API only exposes opaque member IDs and no user search. Display member IDs and select assignees from existing project members.
- No department CRUD, department-derived access, official codes, legal approval, finance, documents, notifications, S3, deployment, or external provider work.
- No fake login, browser-local authorization, bypass of CSRF, persistence of session/CSRF secrets in local storage, or unauthorized-project data fetch.
- Do not change first-slice acceptance statuses or unrelated project documentation.

## Constraints and approved rules

- Use the mandated React, TypeScript, Vite, Tailwind and existing UI primitives.
- Read `/api/v1/auth/session` for the current account, global roles, and CSRF token; keep the token in memory only. Protected reads use `credentials: 'include'`; mutations send `X-CSRF-Token` and rely on existing server checks.
- Only active project members see that project's data. The backend enforces membership and mutation permissions; UI visibility is only a convenience.
- Project Manager may create a project; an in-scope Project Manager may create/assign tasks and archive an active project. Members may transition only their assigned task on the ordinary path. Auditors are read-only. Project archive makes the project read-only.
- Preserve the approved transitions: `open → in_progress`; `in_progress → blocked|done`; `blocked → in_progress`; Project Manager may cancel an unfinished task and reopen `done → in_progress`; `cancelled` is terminal.
- Keep the existing dashboard and safe audit read behavior. Render only the dashboard item matching the selected project; do not display cross-project totals or expose free-form descriptions in audit history.
- Use synthetic fixtures. Do not contact a real IdP or production service.

## Approaches considered

1. **Keep the current single long panel and add controls inline.** Smallest change, but project navigation, task controls, membership, and audit would remain visually crowded.
2. **Build a frontend-only Project Workbench around the existing APIs.** Separates project navigation from project overview, tasks, members, and audit while preserving server contracts. **Selected** because it produces a useful MVP workspace without new business policy or backend scope.
3. **Add backend search, user directory, pagination, and new project APIs first.** Could support richer assignment and larger datasets, but introduces new data/API contracts and is outside the approved first-slice policy.

## Implementation calls

- Use a single workbench route/screen with project navigation and focused project sections/tabs; keep state local to the React app.
- Search projects and filter task rows client-side over only the lists already returned by authorized endpoints.
- Show the current member list by opaque user ID and role. Populate task assignee choices only from those members.
- Render mutation controls only when the current project role/lifecycle permits them; after mutation, refresh relevant project/task/dashboard data and show non-sensitive errors.
- Use existing endpoints only: `/auth/session`, `/projects`, `/projects/{id}`, `/projects/{id}/members`, `/projects/{id}/tasks`, `/tasks/{id}/status`, `/projects/{id}/archive`, `/dashboard/summary`, and `/projects/{id}/audit-events`.
- Keep CHPMIS-007 frontend-only. If existing response contracts cannot support an acceptance item safely, stop and report the gap rather than adding a backend contract or policy.

## Builder check resolution

- Determine the signed-in user and CSRF token from `/api/v1/auth/session`. After loading the selected project's existing member list, match `session.user.id` to a member to derive the user's project role for UI affordances. Global roles are used only for project creation. All reads and mutations remain subject to server-side authorization.
- Existing project creation service atomically creates the creator's project membership with role `project_manager`; no compensating membership flow is needed in the UI.
- Assignee options come from the selected project's returned members. As no user-directory endpoint exists, do not add arbitrary user entry or membership-edit controls.

## Files expected

- `frontend/src/App.tsx` and `frontend/src/components/ProjectTaskManager.tsx` or a focused `ProjectWorkbench.tsx` split following current conventions.
- `frontend/src/App.test.tsx` or focused tests under `frontend/src/**`.
- Existing styles may be updated under `frontend/src/**` only.
- No backend or migration files are in scope.

## Success

An authorized user can navigate an assigned project, see accurate scoped information, find tasks using local filters, and perform approved task actions without a new server policy. An independent Tester and Hermes Reviewer accept the UI behavior and scope; all repository-defined frontend checks pass or are explicitly marked `NOT_VERIFIED`.
