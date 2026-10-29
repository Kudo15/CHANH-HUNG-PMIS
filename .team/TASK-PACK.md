# Task Pack Template

Copy into `.team/tasks/<task-id>.md`. Complete every field and ensure the role has the authority to perform the work. Do not dispatch with unresolved required decisions or missing Worker prompt template.

## Task ID and execution role
- Task ID: TBD
- Role(s): TBD
- Status: PLANNED / BLOCKED / IN_PROGRESS

## Context
Include all relevant requirements, approved decisions, repo state, interfaces, and prior task outputs needed by a clean session.

## Objective
TBD

## Files in scope
- Create/modify: TBD
- Forbidden files: TBD

## Traceability
- Mission / PRD / story / acceptance IDs: TBD

## Acceptance criteria
- [ ] TBD

## Verification command and evidence
- Command: identify a real repository command; if not yet available, mark `NOT_VERIFIED` and state which task creates it.
- Expected evidence: exact output/result and exit code.

## Prompt template
- Library/skill: TBD
- Template name and source: TBD
- Modernized task prompt: TBD
- For non-Worker Human Gate/coordinator tasks, state `NOT_APPLICABLE` with reason.
- For a Worker, do not dispatch if the real template cannot be identified.

## Risks, Human Gates, and boundaries
TBD

## Report format
- Files changed
- Commands run, output summary, exact exit codes
- Acceptance evidence and requirement trace
- Review verdict / findings
- `BLOCKED` / `NOT_VERIFIED` items

## Definition of Done
- [ ] Scope and file boundaries respected.
- [ ] Acceptance criteria evidenced or explicitly marked blocked/unverified.
- [ ] Verification command run and result recorded, or reason for `NOT_VERIFIED` recorded.
- [ ] Required independent review/Human Gate recorded.
- [ ] `.team/ledger.md` updated with observed routing details only.
