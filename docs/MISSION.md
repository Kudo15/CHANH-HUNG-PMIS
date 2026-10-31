# CHÁNH HƯNG PMIS — Mission

## Problem / users
Build a secure web PMIS for the entire Ban QLDA phường Chánh Hưng to manage investment-construction projects, work, cross-department coordination, records, procurement, contracts, progress, capital/disbursement, acceptance/settlement, reports, dashboards, and an AI assistant. Primary users are staff and managers authorized by the Ban QLDA. Exact user groups, departments, titles, decision rights, and identity source are TBD; do not encode them as fixed values.

## Scope
- Modular monolith; MVP modules M01 Dashboard, M02 Projects, M03 Tasks, M04 Workflow, M05 Documents, M06 Notifications, M15 Administration.
- First vertical slice: sign in → create project → assign staff → create/assign task → update task state → view dashboard → inspect audit history.
- Required stack: React + TypeScript + Vite + Tailwind + shadcn/ui; FastAPI + SQLAlchemy 2 + Alembic + Pydantic; PostgreSQL; S3-compatible storage; Docker Compose + CI; Pytest + Vitest + Playwright.
- Secure authentication and server-side RBAC/ABAC across role, department, project scope, workflow state, and document restriction.

## Non-goals
- No stack change without an approved ADR.
- No hardcoded department names, titles, or approval routes; no conflation of internal and statutory/legal approval.
- No production deployment or use of real agency data in development.
- No external LLM access to sensitive records; AI must not invent legal rules or modify official financial values.
- Procurement, contracts, official finance/disbursement, settlement, and statutory approval are outside the first vertical slice.

## Tech constraints
Use the mandated stack and modular-monolith architecture. Use Alembic for schema evolution. Development services bind to localhost. Dependency versions are recorded in existing lockfiles; GitHub Actions is approved for local-first-slice CI checks, with remote execution unverified. Exact IdP, S3 provider, deployment environment and production retention settings remain open.

## Security & privacy
No real agency data in development; no secrets or sensitive documents in Git. Enforce authorization on the backend with least privilege and deny-by-default scope checks. Audit important workflow actions. Legal requirements require authoritative-source verification. Schema, permissions, financial logic, important workflow transitions, and deployment require a Human Gate.

## Definition of Done
Every task has a Task ID, role, bounded scope, DoD, test evidence, and traceability. Report real commands and exit codes; missing evidence is NOT_VERIFIED. Independent review is used when feasible. Obtain required Human Gate approval before risky schema, authorization, financial, approval-workflow, or deployment changes. The first slice must run locally with Compose, migrations, auth, health checks, CI/test setup, and visible audit history.

## Acceptance tests
See `ACCEPTANCE.md`. No criterion is PASS without executed evidence and independent review. HG1–HG5 approve local identity/session foundations, task transitions, authorization and audit behavior. Actual provider connection, initial-admin provisioning, production retention and any policy expansion remain gated.

## Open questions and approvals
See `OPEN_QUESTIONS.md`. HG1–HG5 decisions are approved for the local first slice as of 2026-10-30. Exact production IdP/provider configuration, official retention/privacy schedules, S3/deployment, and legal/finance requirements remain open; do not silently convert assumptions about real processes into policy or code.
