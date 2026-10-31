# Task Pack — CHPMIS-004-R1 Independent Code Review

## Task ID and role
- Task ID: CHPMIS-004-R1
- Role: Hermes Reviewer, independent from Worker and Tester.
- Parent: CHPMIS-004.
- Status: READY AFTER CHPMIS-004-T1 — review after independent Tester reports.

## Objective and authority
Review the CHPMIS-004 implementation diff against the approved task pack, Human Gates, acceptance criteria, Worker evidence, and CHPMIS-004-T1 report. Read-only only: do not edit implementation, tests, docs, or files. Provide `APPROVED` or `CHANGES_REQUESTED`; each required finding must include severity P1/P2/P3, exact `file:line`, impact, and correction direction. This is not a legal/compliance certification.

## Required context
Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, CHPMIS-004 main task pack, this task pack, accepted Human Gate decisions, relevant security/role/data/workflow docs, Tester task and report, then inspect `git status` and the CHPMIS-004 implementation diff. Preserve the dirty baseline and separate preexisting files from the CHPMIS-004 scope where possible.

## Review checklist
- Deny-by-default project membership on list/read/write, non-disclosing errors, no System Admin implicit business access.
- Project Manager in-scope creation/member assignment, role and target validation; no client-controlled creator identity.
- Task assignment requires explicit membership; all task operations resolve and authorize parent project; transitions match approved table exactly.
- Atomic mutation + audit write; restrictive FK/no implicit deletion; no project delete, audit read/export, or audit retention purge.
- Audit payload minimization and allowlist; actor, UTC timestamp, action, IDs, correlation metadata; excludes names/titles/free text, descriptions, credentials, tokens, and document contents.
- Reversible additive migration, data consistency, request/schema validation, exception handling, CSRF/session protections and safe API response shapes.
- Tests meaningfully cover positive/negative cases and rollback; frontend behavior does not imply unapproved capabilities.
- Scope, synthetic-only fixtures, and task file allowlist respected. Track actual provider/DB/browser gaps as `NOT_VERIFIED`.

## Prompt template
- Source: prompts.chat **Senior Code Reviewer (severity-ranked)**, ID `cmv9n79m30005ku060pzornri`, retrieved 2026-10-30: https://prompts.chat/prompts/cmv9n79m30005ku060pzornri_senior-code-reviewer-severity-ranked
- Modernized role prompt: “Apply the Senior Code Reviewer template to CHPMIS-004-R1 as a separate read-only session. Review only the scoped CHPMIS-004 diff and requirements, incorporating but independently assessing Worker and Tester evidence. Prioritize correctness, access control, data integrity, audit atomicity/minimization, migration safety, then maintainability. Do not alter files. Return `APPROVED` or `CHANGES_REQUESTED`; every required finding must state P1/P2/P3, exact file:line, consequence, and concrete correction direction. Do not invent issues or certify legal/compliance status. Finish with exactly one Hermes reviewer action: `kanban_complete(result=...)`, `kanban_request_changes(reason=...)`, or `kanban_block(reason=...)`.”

## Definition of Done
Hermes card contains a verdict, acceptance trace, severity-ranked actionable findings or an explicit no-blockers result, and any unverified infrastructure limitations. Reviewer makes no file changes.


## Hermes card contract

ROLE: reviewer (read-only code review)
Work only inside this task's workspace.
1. Read the approved task pack, charter, ledger, Worker summary, and independent Tester report.
2. Inspect the CHPMIS-004 implementation diff for correctness, scope, authorization, audit, migration, and test quality.
3. Do not modify files or run unlisted commands.
Finish with exactly one of:
- kanban_complete(result=APPROVED or CHANGES_REQUESTED, acceptance trace, findings and evidence)
- kanban_request_changes(reason=concrete required findings)
- kanban_block(reason=why review cannot proceed)

--- REQUIREMENT ---
Follow `.team/tasks/CHPMIS-004-R1-independent-review.md` exactly. Review CHPMIS-004 independently of Worker and Tester, and give severity-ranked file:line findings for any required changes. No implementation edits.
