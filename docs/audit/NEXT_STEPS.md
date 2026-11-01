# Audit Remediation — Next Steps

1. **CHPMIS-014 — canonical bootstrap role**: create a failing bootstrap → valid session → protected System Admin HTTP endpoint test; persist only the canonical enum key; keep legacy display rows inert and block/reconcile explicitly.
2. **CHPMIS-013 — migration/schema/CI** (already reserved in the roadmap for CI): align PostgreSQL schema assertions with head; prove empty and populated prior-schema upgrades on disposable PostgreSQL; repair Ruff and CI Compose interpolation; prove downgrade behavior with bootstrap receipts and never claim unsafe rollback is safe.
3. **CHPMIS-015 — admin approval transactions**: move session revocation into the coordinator-owned transaction, revalidate requester/approver/target authority, serialize decisions, and prove rollback/concurrency on PostgreSQL.
4. **CHPMIS-016 — bootstrap trust boundary**: enforce the approved fixed local synthetic trust-source design in the application; keep real registry provisioning, real approver identity/key custody, and production use gated.
5. **CHPMIS-017 — endpoint authorization matrix**: test every scoped endpoint against PM, Member, Auditor, System Admin, unassigned and multi-role identities using HTTP; close Auditor-only and cross-scope gaps without broadening policy.
6. **CHPMIS-012 — OIDC/browser and synthetic E2E** (already reserved in the roadmap): Vite/API proxy, Compose OIDC configuration, browser-bound one-time state, PKCE, callback return, login/logout/session expiry/error views, issuer/audience/replay checks; then run the full browser → frontend → backend → PostgreSQL → Keycloak journey and negative authorization cases on loopback ports.
7. **CHPMIS-018 — project/task consistency**: PostgreSQL lost-update/concurrency, Project Manager membership consistency, and audit/membership transaction regression, respecting unresolved last-manager policy.
8. **CHPMIS-019 — frontend consistency**: structured 422 rendering, stale response suppression, session-state clearing, and calendar-date/timezone behavior.
9. Recompute the platform gate at the exact final SHA. Start the multi-department vertical slice only if no in-scope P1/P2 findings remain, required tests are non-skipped and pass, remote CI passes that SHA, synthetic E2E passes, and an independent review is accepted.

All tasks run sequentially against the same checkout. Do not start an overlapping worker. Do not push to `master`; any working-branch push is deferred until the scoped diff, secret scan, independent review and exact SHA are verified.
