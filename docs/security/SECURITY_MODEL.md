# Security Model Proposal

## Principles
Least privilege; deny by default; backend authorization authority; department/project isolation; data minimization; auditable important actions; configurable organization policy, not hardcoded units or titles.

## Authentication
Secure authentication is required, but identity source, local-vs-SSO, MFA, session/cookie strategy, recovery, lockout, and provisioning are unresolved. Do not choose a provider or store credentials before owner approval. Keep secrets outside Git.

## Authorization
Combine RBAC grants with ABAC checks for account state, department membership, project scope, workflow state, and document restriction. Check all API paths, IDs, list/search queries, dashboard counts, exports, and future storage access on the server. UI visibility is not authorization.

## Audit
Audit important project, assignment, task, workflow, administrative, and document-access actions. Capture only necessary metadata; never log secrets or document contents. Append-only guarantees, reader privileges, retention, and denied-request policy require security/owner review.

## Data handling
Use synthetic fixtures only. Do not upload agency documents to external LLMs. S3 encryption, malware scanning, signed URL behavior, retention/deletion, backups, and data residency need decisions before M05/deployment.

## Human Gates
Explicit review for schema changes affecting identity/scope/audit, permission matrix, workflow transitions, financial correctness logic, legal approval semantics, secret/provider integrations, and deployment.
