# Task Pack — CHPMIS-001

## Task ID and execution role
- Task ID: CHPMIS-001
- Owner/role: Human Gate owner (project sponsor) with Architect and Security Reviewer
- Status: BLOCKED — awaiting plan review and decisions

## Context and objective
Before implementation of schema, authentication, authorization, task workflow, or audit behavior, decide the open policy items in `OPEN_QUESTIONS.md`. The mission requires Human Gate for these areas. The current architecture/data/API/security/workflow docs are proposals only.

## Files in scope
- Review/update: `OPEN_QUESTIONS.md`, `docs/product/USER_ROLES.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/API_CONTRACT.md`, `docs/workflows/WORKFLOW_CATALOG.md`, `docs/security/SECURITY_MODEL.md`.
- Forbidden: product code, migrations, secrets/provider config, real data, production/deployment changes.

## Traceability
Mission §§2, 4, 6, 7C–E; AC-03, AC-05–AC-13; user stories US-001–US-032.

## Acceptance criteria
- [ ] Identity source/session and account lifecycle decided.
- [ ] Project fields and department/project scope matrix approved.
- [ ] Task states/transitions/authorized actors approved; internal workflow separated from statutory/legal approval.
- [ ] Audit event fields, readers, failure policy, and retention approved.
- [ ] Decisions are written to source docs and explicitly approved before implementation.

## Verification / evidence
- Human decision record in the listed docs; no test command can substitute for this approval.
- Do not mark PASS until the owner explicitly approves the decisions.

## Prompt template
- `NOT_APPLICABLE` — human policy decision / review task, not a Worker task.

## Risks / boundaries
Do not infer policies from candidate role/state examples. No actual department names/titles, legal rule, retention period, or financial rule may be invented.

## Definition of Done
- Decisions and approver are recorded; affected proposals updated; Human Gate status is explicit in ledger; only then may dependent implementation tasks be prepared for dispatch.
