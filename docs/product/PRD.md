# Product Requirements — CHÁNH HƯNG PMIS

## Purpose
Provide the Ban QLDA phường Chánh Hưng with a secure, auditable web workspace for investment-construction project delivery and coordination. Prove a useful end-to-end slice before expanding to specialized procurement, finance, settlement, and AI capabilities.

## Users and roles
The product serves authorized Ban QLDA staff and managers. Exact organizational roles and departments are not supplied; candidate system roles and authorization dimensions are in `USER_ROLES.md` and require validation before enforcement.

## Scope
- **MVP modules:** M01 Dashboard, M02 Projects, M03 Tasks, M04 Workflow, M05 Documents, M06 Notifications, M15 Administration.
- **First slice:** authenticate; create project; assign staff; create/assign task; update task state; see authorized project/task summary; inspect audit events.
- **Later modules:** M07 Procurement, M08 Contracts, M09 Progress, M10 Cost, M11 Capital/Disbursement, M12 Acceptance/Settlement, M13 Reports, M14 AI Assistant, M16 Integrations. Defer until MVP/security gates pass and scope is approved.

## Functional requirements
1. Users authenticate through an approved secure configuration; identity source and session policy are open decisions.
2. Permitted users can create and view projects. Project is the central business aggregate.
3. A project can relate to a lead department, cooperating departments, responsible staff, tasks, documents, procurement packages, contracts, and workflows. The first slice covers project/staff/task relationships only.
4. Permitted users assign staff to projects and tasks, with access checked on the backend.
5. Task state changes use a configurable workflow. Candidate states are provisional and must pass the Human Gate before schema/workflow implementation.
6. Dashboard information is limited to the viewing user's authorized scope; exact widgets and filters are open questions.
7. Important create, assignment, and state-change actions record actor, action, target, timestamp, and minimized safe change context. Retention/personal-data policy requires approval.
8. Administration manages configurable departments, roles/permissions, and workflow definitions; no final organization structure is assumed.

## Non-functional requirements
Use the mandated modular monolith and stack. Backend owns authentication enforcement, authorization, validation, and audit writes. Do not put secrets or real records in Git or development fixtures. Bind development services to localhost. Provide automated backend, frontend, integration, and E2E test capability. Accessibility, performance targets, backup/recovery, retention, and deployment topology are TBD.

## Constraints
Do not send sensitive records to external LLMs. AI is not an authority for legal rules or official financial calculations. Internal workflow approval is distinct from statutory/legal approval. Production deployment needs explicit Human Gate approval.

## Success measure
Complete the vertical slice locally with automated tests, server-side authorization checks, visible audit history, and repeatable setup. Numeric targets and service levels are TBD.

## Traceability
Roles: `USER_ROLES.md`; stories: `USER_STORIES.md`; acceptance: `../../ACCEPTANCE.md`; risks/questions: `../../OPEN_QUESTIONS.md`.
