# CHPMIS-015-F4 — Fix decision-time approver authority revalidation

## Task identity
- **Task ID:** CHPMIS-015-F4
- **Role:** Hermes Backend Worker
- **Parent:** CHPMIS-015, Worker card `t_47da9e47` / run #66
- **Trace:** A5-02, approved HG2, parent task pack `.team/tasks/CHPMIS-015-system-admin-transaction.md`
- **Status:** COMPLETE — F3 regression passes after the fix; final OpenCode verifier and live PostgreSQL rerun passed; independent Reviewer approved with zero findings.

## Objective
Fix the production defect exposed by F3: the approver can become inactive or lose System Admin authority after route-level `validate_session()` returns, yet the approval route may read stale ORM identity-map values and still approve. Keep current approved HG2 semantics and schema unchanged.

## Scope
- Allowed production file: `backend/app/auth/routes.py` only.
- Append a short section to `.team/tasks/CHPMIS-015-worker-report.md`.
- Existing failing regression test is already in `backend/tests/test_auth_remediation.py`; do not edit it or any other test/source/docs/index/ledger/runtime resource.
- No commit, migration, schema change, policy change, Docker/PostgreSQL operation, or real identities.

## Required behavior
1. At decision-time, read the approver's active status and System Admin role freshly from the database within the approval transaction, bypassing stale SQLAlchemy identity-map objects returned by `validate_session()`.
2. If the approver was deactivated or de-authorized after `validate_session()` returns, return HTTP 403; leave the request pending, target role absent, and target session active.
3. Preserve existing dual-control, distinct requester/approver, no-self-grant, requester revalidation, target/action stale checks, one-commit boundary, and safe rollback behavior. Do not add new policy or response changes outside the required fail-closed outcome.
4. The F3 regression `test_system_admin_approval_revalidates_approver_authority_during_decision` must pass both state-change cases.

## TDD and verification
F3 provides the RED evidence: the new regression returned HTTP 200 instead of required 403 against current code (pytest exit 1). First run the exact focused test to confirm RED. Make the smallest production-only fix, then rerun it for GREEN. Run only these repository-defined checks:

From `backend`:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py`
2. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` (report skip if `TEST_DATABASE_URL` is absent; Coordinator owns live PostgreSQL)
3. `.venv\Scripts\python.exe -m pytest -q`
4. `.venv\Scripts\ruff.exe check app/auth/routes.py`
5. `.venv\Scripts\ruff.exe format --check app/auth/routes.py`
From repository root:
6. `git diff --check -- backend/app/auth/routes.py .team/tasks/CHPMIS-015-worker-report.md`

Report exact commands, result summaries, and exit codes. Stop on any test failure; do not weaken or alter tests. No database/runtime checks or other commands are authorized for this card.

## Requirement trace
- Parent acceptance criterion 4: current approver authority must be revalidated in the decision transaction.
- Parent atomicity criterion 2: failed authorization must not commit partial approval/role/session changes.
- HG2: separate existing active System Admin approver; existing policy only.

## Required real prompt template
- prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved 2026-10-31: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Modernized adaptation: “Act as a senior Python/FastAPI/SQLAlchemy engineer. Use the existing failing synthetic regression as RED, then make the smallest production-only change so approver activity and System Admin authority are read fresh during the approval transaction after `validate_session()`; preserve HG2, all existing transaction semantics and public contracts. Do not edit tests or any other product file. Run only the listed checks, append exact evidence, and do not commit.”

## Stop conditions
If the regression cannot be fixed within `backend/app/auth/routes.py` without changing approved authorization semantics, schema, another file, or runtime state, stop and report `BLOCKED` for Coordinator scoping.
