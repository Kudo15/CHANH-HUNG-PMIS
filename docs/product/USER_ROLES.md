# User Roles and Authorization Dimensions

> Approved policy keys for the local first slice as of 2026-10-30. They are not official job titles or a statement of the Chánh Hưng organization; do not seed real departments or titles.

## Approved first-slice roles and actions
- **System Admin:** manages account and role configuration only; no implicit business-data access. Cannot self-grant System Admin. A second existing System Admin approves grants/revocations.
- **Project Manager:** creates and manages projects within granted scope; assigns project members and tasks; manages task transitions, cancellation/reopen, and project archive.
- **Member:** reads explicitly assigned projects and updates state only on tasks assigned to that member, along the approved ordinary work path.
- **Auditor:** reads audit history only for explicitly assigned projects; cannot mutate business data. There is no global auditor role in this slice.

Project scope comes from explicit membership. Department membership alone does not expose cooperating projects. These are application policy keys, not official titles; actual department membership comes from the organization identity source and remains configurable.

## Required authorization dimensions
Every protected request is evaluated server-side using authenticated account state, granted action, department membership, project scope/assignment, workflow state and allowed transition, and document restriction/classification when applicable. Deny by default. Frontend visibility is not an authorization control. Check item reads/writes, lists, search, exports, dashboard aggregates, and future file access.

## Configuration requirements
Departments, titles, role grants, project scope, workflow routes, and document restrictions must be configurable. Do not seed actual agency units/titles until supplied and approved. Internal approval permission is separate from legal/statutory authority.

## Approved decision boundary
Identity/session, the first-slice permission matrix, and project-scoped visibility are approved for local development. Document classification/retention/download controls and any production authorization mapping remain deferred. See `../security/SECURITY_MODEL.md` and `../../OPEN_QUESTIONS.md`.
