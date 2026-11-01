# Task Pack — CHPMIS-017-F1 Independent Review

## Task, role, scope
- Task ID: CHPMIS-017-F1-R1. Role: independent Reviewer, separate session from F1 Worker `t_611c0336`.
- Review the approved F1 change in `backend/app/auth/policy.py` and `backend/tests/test_auth_policy.py`, preserving the existing dirty checkout. Do not edit any file, fix findings, run migrations, use external services, commit, push, or deploy.
- Read `.team/CHARTER.md`, `.team/tasks/CHPMIS-017-F1-missing-project-role.md`, `.team/tasks/CHPMIS-017-F1-worker-report.md`, and the parent endpoint authorization matrix. Inspect the two diffs separately and surrounding production code, resolver callers and relevant tests.

## Required review
- Determine whether assigned project + missing/invalid project role denies access, valid global and project roles intersect correctly, unassigned scope denies, and global project creation remains correct. Examine task-parent resolution, including unresolved parent and consistency between supplied project and task contexts; distinguish current HTTP call paths from helper-only edge cases.
- Check whether caller-supplied `project_role` and database-resolved membership can disagree and assess actual trust boundaries and reachable consequences. Do not assume a finding without tracing callers.
- Confirm fixture changes preserve the old tests' intended role scenarios and the RED test actually covers the previous bypass; evaluate coverage of role combinations and regressions. Identify any gap with exact file/line and concrete impact.
- The Worker report records RED exit 1 and all seven final checks exit 0, including full backend 137 passed/2 skipped. The Worker used an unlisted formatter on the two allowed files after the first format check failed; do not represent the initial check as passing. No need to rerun tests unless review requires it.
- Pre-review SHA-256: `backend/app/auth/policy.py` = `1EB999C57E53C4A72A72423DAA5BAFF4D33241EEADA7AEE9D8DFC200EAF6DACE`; `backend/tests/test_auth_policy.py` = `54A121A215F8E9D29411917C97AAAB715B5E96BE17CCCB1A43B882C129897F0C`. Coordinator verifies both after review.

## Definition of Done
Provide independent criterion-by-criterion assessment and either APPROVED or CHANGES_REQUESTED. Each P1/P2/P3 finding needs precise file:line, trigger, impact and correction direction. Mark incomplete evidence NOT_VERIFIED; do not approve with unresolved P1/P2 or missing required review. Record result through card lifecycle; Coordinator updates ledger and reports.
