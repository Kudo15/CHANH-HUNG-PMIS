# Task Pack — CHPMIS-005-R1 Independent Security Review

## Task ID and role
- Task ID: CHPMIS-005-R1
- Role: Hermes Reviewer (security-focused), independent from Worker and Tester.
- Parent: CHPMIS-005; Worker card `t_0c1b86d4`.
- Status: READY AFTER CHPMIS-005-T1 — review after Tester evidence.

## Objective and authority
Read-only security and quality review of CHPMIS-005 diff against the task pack, approved Human Gates, Worker evidence, and independent Tester report. Do not edit files or implementation. Verdict must be `APPROVED` or `CHANGES_REQUESTED`; required findings state severity P1/P2/P3, exact file:line, impact, and correction direction. This is not legal/compliance certification.

## Required context
Read `AGENTS.md`, charter, ledger, CHPMIS-004/005 task packs, accepted HG2–HG4 policy, relevant security/API/roles docs, Worker summary, Tester evidence, and current `git status`. Inspect only scoped implementation and distinguish earlier baseline changes.

## Review checklist
- Dashboard filters explicit project membership before every count, total, and project list; no cross-project or department-count leakage; no admin implicit access.
- Overdue metric follows task pack semantics; time handling is UTC and centralized.
- Audit reads require explicit project assignment and approved reader role; no Member/global/System Admin bypass, no guessed/cross-project disclosure.
- Audit output allowlists fields on read (not merely trusting sanitized writes); no descriptions/titles/secrets/token/document data or arbitrary JSON leakage.
- Cursor is bounded, stable/newest-first, validated, and scoped to the requested project; tampering/reuse cannot expose another project.
- GET endpoints do not mutate; no export, deletion, retention purge, fake authentication, client-side role authorization, or policy expansion.
- UI calls actual protected APIs with cookies and represents 401/403/404/error states safely; no demo identity/data presented as real.
- Tests meaningfully cover mixed scopes, reader roles, cursor controls, overdue boundaries, and safe fields. Migration/API contract changes stay within task scope.
- Real IdP/browser SSO and live PostgreSQL/Compose gaps remain `NOT_VERIFIED`.

## Prompt template
- Source: prompts.chat **Senior Code Reviewer (severity-ranked)**, ID `cmv9n79m30005ku060pzornri`, retrieved in CHPMIS-004-R1: https://prompts.chat/prompts/cmv9n79m30005ku060pzornri_senior-code-reviewer-severity-ranked
- Modernized Reviewer prompt: “Apply the Senior Code Reviewer template to CHPMIS-005-R1 as an independent read-only security review. Inspect scoped diff and evidence; prioritize aggregate leakage, audit access/field integrity, cursor isolation, session enforcement, read-only behavior, tests, and scope. Do not edit files. Return APPROVED or CHANGES_REQUESTED. Every required finding must cite exact file:line, P1/P2/P3, impact, and correction direction. Do not invent issues or certify legal compliance. Finish with exactly one Hermes reviewer action: `kanban_complete(result=...)`, `kanban_request_changes(reason=...)`, or `kanban_block(reason=...)`.”

## Definition of Done
Reviewer report records verdict, AC-11–AC-13 trace, security gaps/findings, and unverified environment limitations. No Reviewer file changes.


## Hermes Reviewer card contract

ROLE: reviewer (security-focused, read-only)
Work only inside this task's workspace.
1. Read the accepted policy, task pack, Worker summary, and independent Tester report.
2. Review the scoped CHPMIS-005 diff for aggregate leakage, audit access/field integrity, cursor isolation, authentication, UI behavior, and scope.
3. Do not edit files; issue severity-ranked file:line findings.
Finish with exactly one of:
- kanban_complete(result=APPROVED or CHANGES_REQUESTED, acceptance trace and findings)
- kanban_request_changes(reason=concrete required changes)
- kanban_block(reason=why review cannot proceed)

--- REQUIREMENT ---
Follow `.team/tasks/CHPMIS-005-R1-security-review.md` exactly. Independently review Worker implementation and Tester evidence. No file changes.
