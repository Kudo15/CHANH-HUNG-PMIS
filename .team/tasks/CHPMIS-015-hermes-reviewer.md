# CHPMIS-015 — Independent Hermes Reviewer

## Task identity
- **Task ID:** CHPMIS-015-R1
- **Role:** Independent, read-only Reviewer
- **Scope:** Parent CHPMIS-015 implementation plus F3/F4 approver revalidation regression and repair.
- **Trace:** Audit A5-01/A5-02, approved HG2; `.team/tasks/CHPMIS-015-system-admin-transaction.md`.
- **Status:** APPROVED — Hermes Reviewer card `t_53e0ccb8`, run #71/session `20261031_223944_ed8bdc`, default profile, no model/provider override; status done, exit 0, verdict 0 P1/P2/P3. Reviewer made no edits and ran no tests/runtime operations.

## Reviewer contract
Review independently; do not edit implementation or tests, do not run app services or mutate any runtime/database, do not stage/commit. Inspect the task packs, `git status`, relevant source/test diffs, Worker evidence, OpenCode verifier evidence, and Coordinator live PostgreSQL evidence. Use only read-only inspection commands needed to form the verdict. If a requirement is unclear or evidence is insufficient, say so explicitly and request changes or block.

## Review questions
1. Is `revoke_user_sessions()` now part of the approval unit of work without an independent commit? Does the approval route preserve one commit and rollback on failure?
2. Does locking a pending request serialize repeat decisions, and does the PostgreSQL test prove exactly one approval/one conflict with one set of effects?
3. Does decision-time approver revalidation bypass stale ORM identity-map values for both account activity and current System Admin role? Do F3 tests establish that state changes after `validate_session()` return are denied with no target/request side effects?
4. Are requester/approver distinct active System Admins, no-self-grant, target existence and grant/revoke preconditions preserved exactly as approved in HG2, without new business rules?
5. Are changes scoped to the authorized files and all required Worker, OpenCode and live PostgreSQL checks accurately reported? Note any procedural deviations or remaining evidence gaps.

## Evidence to inspect
- `.team/tasks/CHPMIS-015-system-admin-transaction.md`
- `.team/tasks/CHPMIS-015-approver-revalidation-test.md`
- `.team/tasks/CHPMIS-015-approver-revalidation-fix.md`
- `.team/tasks/CHPMIS-015-worker-report.md`
- `.team/tasks/CHPMIS-015-opencode-tester.md`
- `.team/tasks/CHPMIS-015-runtime-evidence.md`
- `backend/app/auth/routes.py`, `backend/app/auth/session.py`
- `backend/tests/test_auth_remediation.py`, `backend/tests/test_postgresql.py`
- Current `git status` and scoped diffs.

## Verdict
Report concrete P1/P2/P3 findings (or zero), evidence and any residual limitations. Do not declare unverified claims PASS. Finish exactly once with `kanban_complete(result=...)`, `kanban_request_changes(reason=...)`, or `kanban_block(reason=...)`.
