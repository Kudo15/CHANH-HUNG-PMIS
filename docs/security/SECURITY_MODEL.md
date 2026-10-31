# Security Model Proposal

## Principles
Least privilege; deny by default; backend authorization authority; department/project isolation; data minimization; auditable important actions; configurable organization policy, not hardcoded units or titles.

## Authentication — approved for local first slice (2026-10-30)
- Use provider-neutral organization OIDC SSO; no public self-registration and no local-password fallback. The exact IdP is not selected; keep endpoint/client configuration external and secrets out of Git.
- The IdP is authoritative for account identity/state and department membership. PMIS project membership remains an explicit app grant.
- MFA is IdP-managed; phishing-resistant authentication should be available. Deprovisioned/denied IdP identities cannot retain an application session.
- Use server-managed opaque sessions in `Secure`, `HttpOnly`, `SameSite=Lax` cookies with CSRF protection, session rotation on login/privilege change, and revocation on logout/deprovision. Local first-slice target: 30-minute idle and 12-hour absolute timeout.

## Authorization — approved for local first slice (2026-10-30)
- Combine approved role permissions with account state and explicit project membership. Department membership alone does not grant project access. Deny by default and validate on every request.
- System Admin manages account/role configuration but receives no implicit business-data access. Project Manager acts only within assigned projects. Member reads assigned projects and changes only own assigned task state. Auditor reads audit only for explicitly assigned projects. No global auditor role in this slice.
- A user cannot self-grant System Admin; a second existing System Admin must approve its grant/revocation. Cross-department cooperation requires explicit project membership.
- Check item routes, lists/search, dashboard aggregates, audit reads, and future file access on the server. For task-ID routes, resolve the parent project and validate project scope before reading/mutating. UI visibility is not authorization.

## Audit — approved for local first slice (2026-10-30)
- Record authentication events, role grants/revocations, project lifecycle/assignment changes, and task assignment/state changes. Store actor, UTC time, action, target/project IDs, correlation ID, and allowlisted before/after values; exclude credentials, tokens, document contents, and free-form descriptions.
- Audit records are append-only at the application level. Reads are project-scoped; no global access or export in this slice.
- Business mutation and audit write are atomic in one transaction. If audit persistence fails, roll back the mutation and return an error.
- Synthetic local data only; no automatic audit deletion for this slice. Production is blocked until an authoritative records-retention and privacy/classification schedule is verified.

## Data handling
Use synthetic fixtures only. Do not upload agency documents to external LLMs. S3 encryption, malware scanning, signed URL behavior, retention/deletion, backups, and data residency need decisions before M05/deployment.

## Human Gates
Explicit review for schema changes affecting identity/scope/audit, permission matrix, workflow transitions, financial correctness logic, legal approval semantics, secret/provider integrations, and deployment.
