# Open Questions and Human Gates

Unanswered items below are blockers when they affect implementation. Use synthetic examples only; do not guess official process, role, legal, or financial rules.

## Human Gate 1 — Identity and account lifecycle
- Is identity managed by a government/organization SSO or by a local account system?
- Are MFA, account recovery, provisioning/deprovisioning, and session duration required?
- Who is the authoritative source for user and department membership?

## Human Gate 2 — Authorization and organizational scope
- Which configurable permissions and role combinations are needed for the first slice?
- How does a user receive project scope: explicit assignment, department membership, or both?
- Which departments may see cooperating projects, and what are separation-of-duties constraints?
- Who may create/assign projects and tasks, update state, view dashboard aggregates, and read audit events?

## Human Gate 3 — Project and task model
- What minimum project fields and unique identifiers are approved for initial creation?
- What task states, meanings, transitions, reopen/cancel behavior, and permitted actors are used in practice?
- Are assignment, reassignment, due dates, and delegation required in the first slice?
- What exact dashboard measures make the MVP useful?

## Human Gate 4 — Audit and privacy
- Which events and before/after fields are recorded, and which data must be excluded?
- Who can read audit history? Is append-only storage required? What are retention and export rules?
- What are the applicable privacy/classification rules for future documents?

## Human Gate 5 — Platform and operations
- Which supported runtime/dependency versions, CI provider, deployment environment, and S3-compatible provider are approved?
- What are performance, availability, backup/recovery, observability, and accessibility targets?
- Confirm that local development ports/services must remain localhost-only (current plan assumes yes).

## Legal / finance gates
- Which official sources and verifier/approver will govern procurement, contract, construction, records, privacy, finance, disbursement, acceptance, and settlement requirements?
- What is the authorized source of official financial values and who may approve any future calculations?
- No legal rule or financial policy is currently verified; see `docs/legal/LEGAL_RULES_REGISTER.md`.

## Tooling blocker
- Prompt-lookup is not currently installed/verified, so no Worker task has been dispatched. Hermes CLI also failed its version check due install-state permissions; no model/provider/profile or GUI information is verified.
