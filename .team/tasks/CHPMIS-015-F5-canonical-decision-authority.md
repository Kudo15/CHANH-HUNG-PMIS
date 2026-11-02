# CHPMIS-015-F5 — Legacy Role Rows Do Not Establish Decision Authority

## Task identity
- **Task ID:** CHPMIS-015-F5
- **Role:** Hermes Backend Worker, then OpenCode read-only verification and separate Hermes Reviewer
- **Parent:** CHPMIS-015 system-admin approval transaction
- **Status:** IN REVIEW — user replied “Approve exact F5 scope” in the trusted chat approval gate on 2026-11-01; Worker implementation is complete and the exact files/behavior remain bounded below.
- **Trace:** mission §4B; CHPMIS-015 approved HG2 and decision-time authority criteria.

## Objective
Keep legacy display-value `System Admin` rows detectable by the bootstrap duplicate/zero-admin guard, but ensure requester and approver decision-time authority accepts only the effective canonical `system_admin` role.

## Scope and boundaries
Allowed product files: `backend/app/auth/routes.py` and `backend/tests/test_auth_remediation.py` only. Append only `.team/tasks/CHPMIS-015-F5-worker-report.md`.

No migration, schema change, role conversion, bootstrap-policy change, new privilege, session policy, dual-control change, real identity, production, staging, or commit. Preserve the F4 decision-time freshness fix, all existing transaction behavior, and bootstrap legacy detection. Use synthetic records only.

## Required RED/GREEN behavior
1. A canonical requester creates a request, then loses the canonical role and receives only a legacy `"System Admin"` row. A different currently authorized canonical admin attempts approval; approval is rejected and the request remains pending with no target role/session side effect.
2. A legacy-only approver cannot establish decision authority even when the request is otherwise pending; verify state remains unchanged.
3. Canonical current requester and approver continue to work under the existing HG2 policy.
4. Bootstrap guard continues to detect legacy rows as a reason to block bootstrap; do not migrate them into authority.

## Verification
From `backend/`, run and report exact output/exit for:
- `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py -k legacy_role`
- `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check app/auth/routes.py tests/test_auth_remediation.py`
- `.venv\Scripts\ruff.exe format --check app/auth/routes.py tests/test_auth_remediation.py`
From repository root:
- `git diff --check -- backend/app/auth/routes.py backend/tests/test_auth_remediation.py .team/tasks/CHPMIS-015-F5-worker-report.md`

Report the PostgreSQL skip if `TEST_DATABASE_URL` is unset; do not claim PostgreSQL evidence from SQLite. After Worker, OpenCode verifier runs feasible read-only checks; separate Hermes Reviewer reads the relevant route, bootstrap guard, test, and task evidence.

## Prompt template
- Found through installed `.agents/skills/prompt-lookup` and retrieved from prompts.chat on 2026-11-01: **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as the CHPMIS-015 backend authorization Worker. Follow HG2 and the CHPMIS-015 transaction contract. Add synthetic RED regressions proving that legacy display-value rows cannot authorize a requester or approver at decision time, then make the smallest route-only correction. Preserve canonical-role behavior, bootstrap detection of legacy rows, F4 freshness checks, transaction/session/request invariants, and existing public contracts. Do not change schema, convert legacy rows, or widen policy. Modify only the allowlist, run only assigned checks, record exact outputs/exits, and request independent review; do not self-approve or commit.”

## Definition of Done
- Required synthetic RED/GREEN regressions and exact checks pass.
- Existing requester/approver transaction and bootstrap duplicate guard are preserved.
- OpenCode verification and independent Hermes Reviewer assessment are recorded.
- Coordinator appends observed evidence and routing to `.team/ledger.md`.

## Hermes card closing contract
ROLE: worker (implementation). Work only in the assigned repository workspace. Follow this pack and keep tasks serialized. Post progress with `kanban_comment`. Finish by calling exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include changed files, exact commands/results/exits, requirement trace and unresolved limits. Do not commit.
