# API Contract Proposal

> Candidate REST contract, not implemented or approved. Authentication/session, state transitions, authorization matrix, and audit exposure require Human Gate.

## Conventions
JSON API; candidate prefix `/api/v1`; stable opaque IDs; Pydantic validation; consistent errors that do not leak protected-record existence. Backend enforces authorization for every endpoint, including lists, aggregates, audit, and future files. Pagination, idempotency, concurrency, and exact error schema remain open.

## Candidate endpoints
- `GET /health/live` — process liveness.
- `GET /health/ready` — database readiness.
- `POST /api/v1/auth/session`, `DELETE /api/v1/auth/session` — candidate session interface; identity mechanism unselected.
- `GET /api/v1/projects` — list authorized projects.
- `POST /api/v1/projects` — create with permission.
- `GET /api/v1/projects/{project_id}` — read within authorized scope.
- `POST /api/v1/projects/{project_id}/assignments` — assign an authorized user.
- `POST /api/v1/projects/{project_id}/tasks` — create project-scoped task.
- `PATCH /api/v1/tasks/{task_id}/status` — apply a configured authorized transition.
- `GET /api/v1/dashboard/summary` — scoped aggregates.
- `GET /api/v1/audit-events` — privileged audit view; fields/retention require approval.

## Security contract
Return a non-disclosing authorization failure for inaccessible records. Never trust client-supplied department/project scope; resolve scope from authenticated identity and grants. A status change checks resource scope and configured current→next state before writing. Successful mutations and denied sensitive attempts follow the approved audit policy.

## Contract verification
After the endpoint/auth shape passes Human Gate, add OpenAPI/schema snapshots and tests for unauthenticated, unauthorized, cross-project, invalid-transition, and allowed requests.
