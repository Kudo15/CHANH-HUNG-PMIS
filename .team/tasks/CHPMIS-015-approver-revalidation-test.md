# CHPMIS-015-F3 — Test approver authority changes before decision transaction

- **Task ID:** CHPMIS-015-F3
- **Role:** Hermes Backend Worker (test-only)
- **Parent:** CHPMIS-015, Hermes Worker card `t_47da9e47` / run #66
- **Trace:** A5-02 and approved HG2; `.team/tasks/CHPMIS-015-system-admin-transaction.md`
- **Status:** COVERAGE DELIVERED — the regression exposed HTTP 200 before F4 and now passes both cases after F4; historical Hermes card `t_f20450c1` remains blocked with the original RED result.

## Objective and identified DoD gap
The current `test_system_admin_approval_revalidates_requester_and_target` covers inactive/de-authorized requester, missing target, and stale grant/revoke. It does not test an approver becoming inactive or losing System Admin authority after `validate_session()` has returned, which is when a stale role list can still pass the route's early guard. The task pack requires decision-time checks for both requester and approver.

## Scope
- Allowed implementation file: `backend/tests/test_auth_remediation.py` only.
- Append a brief section to `.team/tasks/CHPMIS-015-worker-report.md` describing the two approver cases and exact test results.
- Do not edit production code, other tests, models, schema, migrations, task index, ledger, or runtime/DB resources. Do not commit.

## Required test behavior
Add regression coverage for two approval attempts where the authenticated approver is valid during `validate_session()`, then:
1. the approver account is made inactive before the route performs its decision-time checks; and
2. the approver loses the System Admin role before the route performs its decision-time checks.

Use a narrow test monkeypatch/wrapper around the imported route-level `validate_session` function so it first returns the real valid `(session, actor_user, actor_roles)` result, then changes only the synthetic approver state through a separate test session before returning the original result. This makes the existing early role-list guard pass and directly exercises the in-transaction revalidation. Do not mutate production state or use real identities.

For each case, assert HTTP 403 and use a fresh DB session to assert the request remains pending, target role is not granted, and target session remains active. Restore the synthetic approver state between scenarios. Preserve all current assertions and HG2 policy.

## Verification
Run from `backend`:
1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py`
2. `.venv\Scripts\ruff.exe check tests/test_auth_remediation.py`
3. `.venv\Scripts\ruff.exe format --check tests/test_auth_remediation.py`
From repository root:
4. `git diff --check -- backend/tests/test_auth_remediation.py .team/tasks/CHPMIS-015-worker-report.md`

Report exact command/results/exit codes. If the test fails against current code, report the failure and stop; do not edit production code under this test-only card. Coordinator will scope a separate Worker fix if necessary.

## Required real prompt template
- prompts.chat “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved via installed prompt-lookup on 2026-10-31: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- Task adaptation: “Act as a senior Python/FastAPI test engineer. Add only synthetic regression coverage proving the route revalidates approver activity and System Admin role after `validate_session()` returns, using a narrow test wrapper that changes synthetic state between those checks. Assert 403 and unchanged pending request, role, and target sessions. Preserve all existing tests; run only listed checks, append evidence, and do not edit production code or commit.”

## Stop conditions
If a production change, business-policy decision, schema change, or database/runtime mutation is needed, stop and report `BLOCKED` for separate Coordinator scoping.
