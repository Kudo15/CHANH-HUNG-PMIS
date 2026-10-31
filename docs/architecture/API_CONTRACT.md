# API Contract Proposal

> REST contract proposal. Identity/session, first-slice authorization matrix, project/task states, and audit scope were approved for local development on 2026-10-30. Production provider configuration and retention remain gated.

## Conventions
JSON API; candidate prefix `/api/v1`; stable opaque IDs; Pydantic validation; consistent errors that do not leak protected-record existence. Backend enforces authorization for every endpoint, including lists, aggregates, audit, and future files. Pagination, idempotency, concurrency, and exact error schema remain open.

## Candidate endpoints
- `GET /health/live` — process liveness.
- `GET /health/ready` — database readiness.
- `GET /api/v1/auth/login`, `GET /api/v1/auth/callback`, `GET /api/v1/auth/session`, `DELETE /api/v1/auth/session` — provider-neutral OIDC login/callback and server-managed session; exact IdP configuration is external and unselected.
- `GET /api/v1/projects` — list authorized projects.
- `POST /api/v1/projects` — create with permission.
- `GET /api/v1/projects/{project_id}` — read within authorized scope.
- `POST /api/v1/projects/{project_id}/assignments` — assign an authorized user.
- `POST /api/v1/projects/{project_id}/tasks` — create project-scoped task.
- `PATCH /api/v1/tasks/{task_id}/status` — apply a configured authorized transition.
- `GET /api/v1/dashboard/summary` — scoped aggregates; returns status counts and overdue counts derived strictly after server-side project membership is enforced. Overdue is centralized as due_date < current UTC instant excluding terminal states (done, cancelled).
- `GET /api/v1/projects/{project_id}/audit-events` — project-scoped audit view for an explicitly assigned Auditor or in-scope Project Manager. Bounded cursor pagination (limit capped at 100), stable newest-first ordering, strictly allowlisted safe fields only (no descriptions, titles, or secrets). Guessed, cross-project, member, and unrelated admin requests fail closed (404). No global audit collection endpoint or export in this slice.

## Security contract
Return a non-disclosing authorization failure for inaccessible records. Never trust client-supplied department/project scope; resolve scope from authenticated identity and grants. A status change checks resource scope and configured current→next state before writing. Successful mutations and denied sensitive attempts follow the approved audit policy.

For task-ID routes such as `PATCH /api/v1/tasks/{task_id}/status`, resolve the task parent project and enforce the caller approved project scope before reading or mutating the task. Do not authorize solely from possession of a task ID.

## Contract verification
After the endpoint/auth shape passes Human Gate, add OpenAPI/schema snapshots and tests for unauthenticated, unauthorized, cross-project, invalid-transition, and allowed requests.
