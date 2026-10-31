# Data Model Proposal

> The local-first-slice schema below was approved by the project owner on 2026-10-30. Production-only requirements remain separately gated.

## Candidate entities
- **User:** stable internal ID, identity-provider subject or approved local identity reference, account state; no credential secrets here.
- **Department:** configurable organizational unit; no names/hierarchy seeded without approval.
- **Role / Permission / UserRole:** configurable grants and scope constraints; no fixed official titles.
- **Project:** generated opaque ID, required name, optional description, configurable lead-department reference, assigned Project Manager, optional start/end dates, and `active`/`archived` lifecycle. No official code scheme or deletion is introduced.
- **ProjectDepartment:** lead/cooperating department relationships, configurable and auditable.
- **ProjectAssignment:** user-to-project association and responsibility type as configurable data; effective dates if approved.
- **Task:** project-scoped work item with title, optional description, creator, optional assignee/due date, approved state, and timestamps.
- **TaskAssignment:** explicit assignment and history if reassignment must be auditable.
- **WorkflowDefinition / Transition:** configurable transition policy; do not encode statutory approvals as internal transitions.
- **AuditEvent:** actor, action, target type/ID, UTC timestamp, project ID, correlation ID, and allowlisted before/after context. Application writes are append-only; mutation and audit write share one transaction. Local synthetic data has no automatic audit deletion; production retention remains blocked pending an authoritative schedule.
- **Document metadata / Object reference:** deferred; bytes in S3-compatible store, restriction checked server-side.

## Relationship sketch
User ↔ Department membership; User ↔ Role grants; Project ↔ Departments; Project ↔ Users through assignments; Project → Tasks; Task ↔ Users through assignment; important writes → AuditEvent. Workflow definitions govern task transitions. These are candidates, not a migration specification.

## Constraints and unresolved decisions
Use foreign keys and transactions; prevent cross-project task references. Apply least privilege to audit and documents. Avoid secrets, document content, and free-form descriptions in audit payloads. The first-slice decisions for identity, roles/scope, project/task fields, states, and audit transaction/access are recorded in `OPEN_QUESTIONS.md`; no financial schema is approved. Department hierarchy, official project-code formats, production retention/privacy, concurrency strategy beyond safe transactions, and future finance precision/currency remain outside this local-first-slice approval.
