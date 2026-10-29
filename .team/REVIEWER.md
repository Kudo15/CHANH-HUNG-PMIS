# Reviewer Protocol

Use a clean session. Read `AGENTS.md`, `.team/CHARTER.md`, the task pack, and the changed files/diff.

## Pass 1: Specification and boundaries
Check the task objective, allowed/forbidden files, acceptance criteria, and Definition of Done. Identify any unapproved scope expansion or unsupported completion claim.

## Pass 2: Quality and safety
Check correctness, maintainability, security/privacy, secret handling, localhost binding for local services, and whether verification evidence matches the actual commands and results.

## Verdict
Conclude with exactly one of:
- `APPROVED`
- `CHANGES_REQUESTED`

For every finding, provide `file:line`, priority (`P1`, `P2`, or `P3`), the concrete issue, and a correction direction. If evidence is unavailable, say `NOT_VERIFIED`; do not infer a pass.
