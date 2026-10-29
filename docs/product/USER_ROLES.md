# User Roles and Authorization Dimensions

> Proposal only, not a statement of official Chánh Hưng organization. Validate before seeding roles or enforcing a permission matrix.

## Candidate personas
- **System administrator:** configures accounts, departments, roles, permissions, and settings; receives no automatic business approval authority.
- **Project manager / responsible officer:** manages assigned projects and tasks within granted scope.
- **Department coordinator:** coordinates assigned department participation and work within project scope.
- **Viewer / manager:** reads authorized project/dashboard information; write or approval rights are not inferred from title.
- **Records operator:** handles documents only when assigned and permitted by their restriction level.

Names are placeholders. Do not hardcode these as stable official role keys or map them to job titles without approval.

## Required authorization dimensions
Every protected request is evaluated server-side using authenticated account state, granted action, department membership, project scope/assignment, workflow state and allowed transition, and document restriction/classification when applicable. Deny by default. Frontend visibility is not an authorization control. Check item reads/writes, lists, search, exports, dashboard aggregates, and future file access.

## Configuration requirements
Departments, titles, role grants, project scope, workflow routes, and document restrictions must be configurable. Do not seed actual agency units/titles until supplied and approved. Internal approval permission is separate from legal/statutory authority.

## Human Gate decisions
Identity source and provisioning; permission matrix and separation of duties; default project and cross-department visibility; document classification/retention/download controls; audit access and retention. See `../security/SECURITY_MODEL.md` and `../../OPEN_QUESTIONS.md`.
