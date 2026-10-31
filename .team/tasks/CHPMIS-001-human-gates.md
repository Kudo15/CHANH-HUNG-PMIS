# Task Pack — CHPMIS-001

## Task ID and execution role
- Task ID: CHPMIS-001
- Owner/role: Human Gate owner (project sponsor) with Architect and Security Reviewer
- Status: COMPLETE for the local first slice — project owner approved the complete HG1–HG5 recommendation package in chat on 2026-10-30. Production/legal items remain separately blocked.

## Context and objective
Before implementation of schema, authentication, authorization, task workflow, or audit behavior, decide the open policy items in `OPEN_QUESTIONS.md`. The mission requires Human Gate for these areas. The current architecture/data/API/security/workflow docs are proposals only.

## Files in scope
- Review/update: `OPEN_QUESTIONS.md`, `docs/product/USER_ROLES.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/API_CONTRACT.md`, `docs/workflows/WORKFLOW_CATALOG.md`, `docs/security/SECURITY_MODEL.md`.
- Forbidden: product code, migrations, secrets/provider config, real data, production/deployment changes.

## Traceability
Mission §§2, 4, 6, 7C–E; AC-03, AC-05–AC-13; user stories US-001–US-032.

## Acceptance criteria
- [x] Identity source/session and account lifecycle approved for local first slice.
- [x] Project fields and department/project scope matrix approved for local first slice.
- [x] Task states/transitions/authorized actors approved; internal workflow separated from statutory/legal approval.
- [x] Audit events, readers, failure behavior, and local-only retention boundary approved. Production retention remains blocked pending authoritative records schedule.
- [x] Decision record and approval date written to source docs before implementation.

## Verification / evidence
- Human decision record in the listed docs; no test command can substitute for this approval.
- Owner approval is recorded for local-first-slice decisions. This does not approve legal policy, production, or external-provider configuration.

## Prompt template
- `NOT_APPLICABLE` — human policy decision / review task, not a Worker task.

## Risks / boundaries
Do not infer policies from candidate role/state examples. No actual department names/titles, legal rule, retention period, or financial rule may be invented.

## Definition of Done
- Decisions and approver are recorded; affected proposals updated; Human Gate status is explicit in ledger; only then may dependent implementation tasks be prepared for dispatch.
