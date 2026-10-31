# CHPMIS-011 — Local OIDC verification and initial admin bootstrap design

**Status: APPROVED for local synthetic implementation by owner on 2026-10-31.** Actual agency IdP, official approver/key nominations, real identities, production grants and deployment remain separately gated.

## Intent
Verify the existing OIDC/session implementation against a real but local-only identity provider, and define a safe way to provision the first two System Admins without weakening the established two-person grant rule. This closes AC-05 evidence for the local first slice; it does not connect the agency IdP or prove production readiness.

## Current state

- `backend/app/auth/oidc.py` has a provider-neutral boundary and `DefaultOIDCClient` intentionally raises `NotImplementedError`. Mock OIDC tests cover signed-token validation and session creation.
- `backend/app/config.py` externalizes issuer/client/endpoints/JWKS/callback settings. No actual provider is configured.
- First successful callback creates a User without a role.
- The ordinary System Admin grant endpoint requires an already active System Admin, creates a request and requires a distinct existing System Admin to approve. There is no bootstrap path.
- `UserRole.granted_by` is required; ordinary grant history cannot honestly represent a grant authorized before any System Admin existed. Do not fake an existing administrator or silently treat the two targets as pre-existing approvers.
- `.team/CHARTER.md`, `OPEN_QUESTIONS.md`, and CHPMIS-003 packs prohibit real provider calls and initial-admin bootstrap until a separate owner decision.

## Goals

1. Add an optional, synthetic-only, local Keycloak test realm to the existing Compose development environment, bound to loopback, with no agency provider or identity data.
2. Exercise real authorization-code OIDC discovery/token exchange, signature/issuer/audience/nonce validation, callback, and resulting session/cookie behavior against Keycloak. Preserve the fail-closed default when provider settings are absent.
3. Define a one-time, offline initial-admin procedure requiring two distinct human approvals. It applies to exactly two distinct, active OIDC user records after their first login; neither can self-authorize the other's grant by pretending an application admin already exists.
4. Preserve durable, truthful bootstrap provenance separately from ordinary dual-control grants. No credentials, names, emails, or agency identifiers in Git.
5. Keep all local published ports on `127.0.0.1`; use synthetic accounts and process-only generated secrets.

## Non-goals

- Connect or select the actual organization IdP, import real identities, obtain agency credentials, or call any external identity provider.
- Change MFA, role meanings, project authorization, session policy, self-registration, or normal two-admin approval rules.
- Automatically seed admins, allow self-grant, make the bootstrap repeatable, or weaken the no-admin fail-closed state.
- Verify the complete authenticated project/task E2E path (proposed CHPMIS-012), remote CI (AC-04), production identity or compliance.
- Stage/commit, push, deploy, or use production.

## Approaches considered

### Identity provider

1. **Local Keycloak test realm — selected by owner.** Exercises actual OIDC redirects, discovery and tokens with synthetic users; keeps agency identity and provider access out of scope. Costs a local container, realm/client setup and careful issuer/backchannel URL handling.
2. **Organization non-production IdP.** Closest to eventual federation, but requires agency approval, tenant details, account nomination, registration and secret exchange. It would introduce an external provider and remains unauthorized.
3. **Continue deterministic mocks only.** Lowest setup cost, but does not verify real OIDC protocol interoperability and cannot close AC-05. Not sufficient for CHPMIS-011's intended verification.

### Initial administrators

1. **One-time offline, two-person approval — selected by owner.** A controlled operator procedure, outside the application grant API, validates exactly two distinct active OIDC users and requires two separately attributable approvals. It runs only on a database with no System Admin grants and writes grants plus durable bootstrap provenance atomically. A permanent consumed marker makes replay fail. This must not encode either target as an ordinary requester/approver or fabricate an existing admin. Proposed approver roles for the local synthetic process: project owner and a distinct independent Security Reviewer. This does not assert which real agency officials have authority; that nomination remains a later organization decision.
2. **Map an organization-controlled IdP admin group.** Avoids local bootstrap code but turns an IdP claim/group into authorization policy and requires the actual organization's claim semantics and approval; not selected and not authorized.
3. **Defer initial admin role provisioning.** Keeps all privileged account setup out of CHPMIS but leaves a usable protected app and AC-05 admin journey unverified. This is the fallback if a truthful two-person evidence mechanism cannot be approved.

## Proposed design (not yet approved)

### Local Keycloak

- Add an opt-in Compose profile/service for a pinned official Keycloak image after official version/configuration verification during planning. Do not silently add it to the default stack.
- Bind the browser-facing IdP port to `127.0.0.1`; keep service-to-service traffic on the Compose network. Use a fixed public issuer and browser authorization URL at `http://127.0.0.1:<published-port>/realms/<synthetic-realm>`, while configuring backend-only token/JWKS URLs on the Compose network (for example `http://keycloak:8080/...`). This uses the existing separate issuer, authorization, token and JWKS settings; verify the public discovery issuer and the configured internal backchannel independently. Keep Keycloak hostname strict/fixed; do not trust dynamic Host headers or broaden port bindings. Exact port/path/image are planning-time choices.
- Use a disposable realm/client and synthetic users created at runtime. Generate all admin and test-user credentials per run, keep them process-local or in ignored local state, and never print them. Import no real group, department or identity claims.
- Add teardown instructions that stop/remove only this task's Keycloak service and preserve unrelated Compose services/volumes. Local Keycloak's development mode is not an approved deployment posture.

### Initial two-admin bootstrap

- Keep bootstrap outside regular HTTP endpoints and normal login. It requires an already initialized schema, exactly zero System Admin role rows, exactly two distinct active users whose OIDC accounts were created through successful login, and a bound environment/instance confirmation.
- Require two independent approvals tied to the exact environment and the exact pair of user IDs; reject same-person approval, stale/replayed/changed-payload approvals, inactive/missing users, a third/fewer targets, or any existing admin role.
- Apply both grants in one transaction. Persist an append-only bootstrap receipt identifying the two authorizers, target user IDs, operator, environment/instance, timestamp, and consumed status. Keep this receipt structurally distinct from ordinary `granted_by`/`approver_id` history. No secrets or personal identifiers in source or committed fixtures; actual production identifiers would stay in protected runtime records.
- Stop if the two approvals cannot be authenticated and durably represented without inventing a service identity or misusing existing grant fields. Bring the precise schema/policy alternative back to the owner; do not make a one-person DBA shortcut. Proposed execution interface is a one-time offline operator CLI, not an app endpoint. Proposed durable receipt is a separate append-only table with opaque target/approver user IDs, environment identifier, approval references, executor, timestamps and consumed status; no names/emails or approval secrets in source. The CLI must require both approval attestations bound to the exact environment and target pair and atomically record the receipt with the role rows.
- Ordinary grant/revocation after bootstrap continues using the existing distinct-active-System-Admin request/approval API.

### Verification

- Use only generated synthetic users in the disposable Keycloak realm and local PostgreSQL database. Verify the actual OIDC round trip and cookie/session properties: opaque session cookie `HttpOnly`, `Secure`, `SameSite=Lax`; CSRF and logout/revocation behavior as applicable to the existing approved policy.
- Verify invalid issuer, audience, nonce, signature, missing/expired claims and unknown key fail closed against the actual local provider where feasible; retain existing deterministic negative tests.
- Verify bootstrap tests: valid two-person approval; same-person/forged/stale/replayed approval denied; wrong environment, wrong user count, inactive account, or pre-existing admin denied; transaction rollback leaves no partial grants; repeat invocation fails; normal post-bootstrap dual-control grants remain unchanged.
- Capture exact commands/results, generated runtime configuration without secrets, actual bound addresses, migration state, and independent review. No actual organization IdP call.

## Security and policy gates

Owner explicitly approved this complete local design on 2026-10-31 and directed immediate execution. This authorizes the opt-in local Keycloak profile, synthetic-only realm/client, scoped OIDC implementation, additive local bootstrap receipt/migration/CLI, generated process-only local credentials, and local verification described here. It does not authorize connecting an external provider, using real identities/credentials, production grants, deployment, remote access, or changes to ordinary grant/revocation policy.

The owner approved the four local implementation decisions on 2026-10-31. They are now bound by the task pack and implementation plan. This approval does not extend to actual agency IdP selection, real approver/key nominations or custody, real identities, production grants, or deployment.

Actual organization IdP selection, agency identity nomination, and network/secret configuration require a later separate approval; the two target identities must be nominated outside Git/chat.

## Open questions for later Human Gate

- Which actual agency IdP, issuer/client registration, network routes, and secret exchange are authorized for a future environment?
- Who are the actual Project Owner and independent Security Reviewer approvers, and how are their signing keys issued, verified, stored and revoked? Do not post identities or key material in Git/chat.
- What retention and privacy requirements govern receipts and approval evidence in any non-synthetic environment?
- What protected runtime environment may hold real approver public keys and receive any real bootstrap grants?

## Approval state

Owner approved this design on 2026-10-31 and said “duyệt, tiến hành ngay.” Implementation is authorized within the local synthetic boundary above. The approved roles are Project Owner and a distinct Security Reviewer. The implementation plan uses separate Ed25519 approval attestations bound to the exact local environment and ordered target pair; private keys remain offline/process-only and no actual authority is inferred from local test keys. Official approver/key ownership and actual agency identities remain open for a later Human Gate.

## Builder-check review and coordinator calls

A fresh builder check identified four planning questions. Coordinator resolutions for technical choices: Keycloak exposes separate frontend and backchannel endpoint URLs; set a fixed loopback hostname/issuer and configure public browser authorization separately from private Compose token/JWKS backchannels, using the existing settings. Keycloak documentation describes its fixed `hostname` as the source for frontend URLs and a separate backchannel URL capability; hostname options affect advertised endpoints, not listen bindings. The implementation plan must verify metadata/issuer/endpoints on both paths and keep the hostname fixed. Official source: https://www.keycloak.org/server/hostname (checked 2026-10-31).

“Offline one-time” is resolved as a narrowly scoped operator CLI, outside HTTP/login. This is a Coordinator interpretation for the design; owner approval is still required. Proposed local synthetic approvers are the project owner and a distinct Security Reviewer, with approvals bound to the pair/environment and independently attributable. Actual organizational nominators/approvers remain unknown and must not be inferred. A dedicated append-only receipt table is proposed because existing UserRole.granted_by cannot truthfully represent a pre-existing application administrator; the table and migration remain gated pending approval.
