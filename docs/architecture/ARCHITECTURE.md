# Architecture Proposal

## Status
Proposed modular-monolith architecture based on the required stack. This does not approve production topology, identity provider, or detailed authorization/schema design. Schema, authorization, key workflows, and deployment changes require Human Gate.

## Components
- **Web:** React + TypeScript + Vite; Tailwind and shadcn/ui; versioned HTTP API.
- **API:** FastAPI; Pydantic contracts; SQLAlchemy 2 persistence. Owns authentication enforcement, authorization, business validation, and audit writes.
- **Database:** PostgreSQL with Alembic migrations. Project is the central aggregate; modules remain packages/services inside one deployable backend.
- **Object storage:** S3-compatible for future documents. Not needed for the first slice; provider, encryption, scanning, and retention are undecided.
- **Local infrastructure:** Docker Compose for web, API, and PostgreSQL; localhost-only published ports; API/database health checks.
- **CI:** automated formatting/static checks and backend/frontend tests; provider TBD.
- **AI:** deferred, separate service; no provider or sensitive data access without approval.

## Module boundaries
M01 Dashboard reads authorized project/task summaries. M02 Projects owns project data and membership. M03 Tasks owns project-scoped tasks and assignments. M04 Workflow owns configurable transitions; MVP task workflow needs approval. M05 Documents owns metadata and object access. M06 Notifications consumes authorized domain events. M15 Administration owns configurable departments, permissions, and workflow definitions. Other modules are deferred.

## Request flow
Browser → API authentication → server-side authorization (identity, permission, department/project/workflow/document scope) → module service validation → transaction/persistence → audit event → response. Lists and dashboard aggregates apply the same authorization as item endpoints.

## Reliability and operations
Separate process liveness from database readiness. Migrations run explicitly; startup must not silently destroy/reset data. Local Compose uses synthetic data only. Backups, recovery, production topology, observability, and service objectives are open decisions.

## Decisions
The mandated stack and modular monolith are fixed. No real-data use or production deployment in this phase. Session/token mechanism, API versioning details, module schema ownership, storage vendor, CI platform, and operations settings remain open. See `DATA_MODEL.md`, `API_CONTRACT.md`, `../security/SECURITY_MODEL.md`, and `../../OPEN_QUESTIONS.md`.
