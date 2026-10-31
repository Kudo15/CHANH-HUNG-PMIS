# Task Pack — CHPMIS-003-F1 Independent Security Review

## Task and role
- Task ID: CHPMIS-003-F1-SR1
- Role: independent Security Reviewer / read-only
- Status: READY TO DISPATCH
- Target Worker card/session: `t_5b6a5d8c` / `20261030_094108_d81b52`

## Scope and acceptance
Review only the CHPMIS-003-F1 diff against `.team/tasks/CHPMIS-003-F1-auth-security-remediation.md` and the four prior findings recorded in `.team/tasks/CHPMIS-003-security-review.md`. Do not modify implementation, tests, task packs, acceptance, or ledger. Inspect signature/JWKS/claim validation and no-user-write-on-failure; authenticated two-person grant/revoke, self-grant/self-approval/replay controls and durable history; fixed callback URI; bounded expired OIDC-state cleanup; migration reversibility; and scope adherence. Report `APPROVED`, `CHANGES_REQUESTED`, or `BLOCKED`, with severity, file and line for each finding. Do not treat test results as security certification. No real IdP calls, deployment, or production access.

## Prompt template
- Library: prompts.chat via `.agents/skills/prompt-lookup`.
- Template: **Vulnerability Auditor Agent Role**, ID `cmmx31zon000dk604l`, retrieved 2026-10-30 and adapted read-only.
- Modernized prompt: “Perform an independent, read-only security review of CHPMIS-003-F1. Verify each prior finding against the diff and assess cryptographic verification, claims, role dual-control, callback binding, state cleanup, migration safety, and scope. Do not change files or call an IdP. Return APPROVED, CHANGES_REQUESTED, or BLOCKED with concrete severity and file:line evidence. State what remains NOT_VERIFIED.”

## DoD
- Independent read-only reviewer records a verdict and concrete evidence for all four findings and scoped risks.
