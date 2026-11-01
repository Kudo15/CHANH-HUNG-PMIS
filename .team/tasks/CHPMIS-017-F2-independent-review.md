# Task Pack — CHPMIS-017-F2 Independent Review

## Role and scope
- Task ID CHPMIS-017-F2-R1; independent Hermes Reviewer, separate session from Worker `t_1ef0b522`. Owner approved F2 and independent review.
- Review only; do not edit, stage, commit, deploy, use external services or alter the dirty workspace. Coordinator updates ledger.
- Read `.team/CHARTER.md`, `.team/tasks/CHPMIS-017-F2-task-context-proposal.md`, `.team/tasks/CHPMIS-017-F2-worker-report.md`, the parent matrix, and inspect `backend/app/auth/policy.py`, `backend/tests/test_auth_policy.py`, resolver implementation and HTTP task callers. The diff versus HEAD also includes earlier CHPMIS-017 and F1 work; distinguish F2 changes using its report.

## Review criteria
- Trace task/project mismatch and unresolved task parent; confirm both fail closed and the RED regression actually covered the prior behavior. Confirm matching identifiers, task-only context, role intersections and global project creation remain correct.
- Inspect the actual resolver and task-detail/transition HTTP callers. Check that the extra parent lookup cannot produce an incorrect project decision or regress valid calls; distinguish demonstrated bugs from possible future misuse.
- Review test assertions for real authorization outcomes, including PM and Member cases, and check meaningful boundary coverage. Report any security or regression finding with precise file:line, trigger, impact and correction direction.
- The Worker report records RED and seven final checks exit 0, full backend `138 passed, 2 skipped`. Initial Ruff and format checks failed before cleanup; Worker ran an unlisted formatter on the two allowed files then reran all seven checks. No need to rerun tests unless needed for a concrete concern.
- Pre-review SHA-256: policy `53E6BEA8E7C8B0DEA63A595B8B0154BDB8906C66D04CAC4C165F9E56D7C5F54A`; test `605BAE02F43DE4CCEE346A3049A89BF5631888C6FCDD7AD16D11006BDD4954BF`. Coordinator checks hashes after review.

## Definition of Done
Return criterion-by-criterion assessment and `APPROVED` or `CHANGES_REQUESTED`; include P1/P2/P3 findings with evidence and any NOT_VERIFIED limits. No approval with unresolved P1/P2 or incomplete required review. Record result through card lifecycle.

## Review result — 2026-11-01
Hermes Reviewer card `t_afd09e45`, run #86, session `20261101_204011_0818a8`, default profile, reported APPROVED with zero P1/P2/P3. The Reviewer inspected policy, test, database resolver and HTTP callers, and cited the Worker's RED/GREEN and checks rather than rerunning tests. Coordinator rechecked the two SHA-256 values after the review; both match the values above. No source edit was observed.
