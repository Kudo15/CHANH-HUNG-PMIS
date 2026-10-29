# Data Model Proposal

> Conceptual only. No schema/migration is approved here. Identity, authorization, workflow, and audit schema require Human Gate.

## Candidate entities
- **User:** stable internal ID, identity-provider subject or approved local identity reference, account state; no credential secrets here.
- **Department:** configurable organizational unit; no names/hierarchy seeded without approval.
- **Role / Permission / UserRole:** configurable grants and scope constraints; no fixed official titles.
- **Project:** central aggregate with stable ID, approved fields, lifecycle state, lead department reference.
- **ProjectDepartment:** lead/cooperating department relationships, configurable and auditable.
- **ProjectAssignment:** user-to-project association and responsibility type as configurable data; effective dates if approved.
- **Task:** project-scoped work item, assignee/creator references, configurable state; due date only if approved.
- **TaskAssignment:** explicit assignment and history if reassignment must be auditable.
- **WorkflowDefinition / Transition:** configurable transition policy; do not encode statutory approvals as internal transitions.
- **AuditEvent:** actor, action, target type/ID, timestamp, correlation ID, minimized change context. Append-only and retention require approval.
- **Document metadata / Object reference:** deferred; bytes in S3-compatible store, restriction checked server-side.

## Relationship sketch
User ↔ Department membership; User ↔ Role grants; Project ↔ Departments; Project ↔ Users through assignments; Project → Tasks; Task ↔ Users through assignment; important writes → AuditEvent. Workflow definitions govern task transitions. These are candidates, not a migration specification.

## Constraints and unresolved decisions
Use foreign keys and transactions; prevent cross-project task references. Apply least privilege to audit and documents. Avoid sensitive content in logs. Before migration decide project fields/identifier, department hierarchy, identity model, role/scope representation, task states, audit immutability/payload/retention, archive vs soft delete, concurrency, and future financial precision/currency. No financial schema is in the first slice.
