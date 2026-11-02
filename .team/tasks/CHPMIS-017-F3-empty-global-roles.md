# CHPMIS-017-F3 — Empty Global Roles Must Deny Business Reads

## Task identity
- **Task ID:** CHPMIS-017-F3
- **Role:** Hermes Backend Worker, then OpenCode read-only verification and separate Hermes Reviewer
- **Parent:** CHPMIS-017 endpoint authorization matrix
- **Status:** COMPLETE for local scope — Hermes Worker `t_e4f5224f`, bounded OpenCode verifier run `2026-11-01T14-43-04-verifier-chpmis-017-f3-bounded-opencode-checks-8dcb`, Coordinator checks, and independent Hermes Reviewer `t_fce4ffa1` APPROVED (0 findings). The earlier OpenCode timeout remains historical evidence and is not counted as a pass.
- **Trace:** mission §4A; approved CHPMIS-017 deny-by-default intersection contract; A4-01/A4-02.

## Objective
Reproduce and close the empty-global-role membership leak in project listing and dashboard reads. Keep `authorize()`'s existing deny for `roles=[]`, preserve intersection semantics, and do not add permissions.

## Scope and boundaries
Allowed product files: `backend/app/projects/routes.py`, `backend/app/projects/service.py`, `backend/tests/test_projects.py`, `backend/tests/test_dashboard_audit.py`, `backend/tests/test_tasks_workflow.py`, and `backend/tests/test_auth_policy.py` only if a regression proves a shared-helper issue. Append only `.team/tasks/CHPMIS-017-F3-worker-report.md`.

Use synthetic users, sessions, memberships, projects, tasks, and audit rows only. Do not change schema, migrations, role permissions, UI, external identity, deployment, or unrelated task evidence. Do not stage or commit. Preserve all current files. If changing `actor_roles=None` semantics would affect callers without an approved authenticated-policy contract, stop and record the callsite/evidence instead of guessing.

## Required RED/GREEN behavior
1. With a valid session and project membership but zero `UserRole` rows, `GET /api/v1/projects` and `GET /api/v1/dashboard/summary` disclose neither rows nor counts.
2. Revoke a user's final global role while leaving membership intact; subsequent list/dashboard reads disclose no business data.
3. Check the existing detail, task, member, and audit endpoints for consistent denial under zero global roles; no copied policy with dummy/fake context.
4. Unknown roles and multi-role combinations continue to follow the approved intersection policy; do not convert intersection to union or grant auditor/admin business access.
5. Confirm `authorize(roles=[])` remains denied. Review optional `actor_roles=None` service callsites; add no bypass or silently change unapproved non-route semantics.

## Verification
From repository root, run and report each exact output and exit code:
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py -k empty_global_roles`
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_dashboard_audit.py -k empty_global_roles`
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_projects.py backend/tests/test_tasks_workflow.py backend/tests/test_dashboard_audit.py`
- `./backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_auth_policy.py`
- `./backend/.venv/Scripts/ruff.exe check --config backend/pyproject.toml backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py`
- `./backend/.venv/Scripts/ruff.exe format --check backend/app/projects/routes.py backend/app/projects/service.py backend/tests/test_projects.py backend/tests/test_dashboard_audit.py backend/tests/test_tasks_workflow.py backend/tests/test_auth_policy.py`
- `git diff --check`

After Worker: independent OpenCode verifier runs the assigned feasible checks read-only; separate Hermes Reviewer reads the full relevant code/callers and reviews every criterion. No tests may be represented as passing if skipped or blocked.

## Prompt template
- Found through installed `.agents/skills/prompt-lookup` and retrieved from prompts.chat on 2026-11-01: **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as the CHPMIS-017 backend authorization Worker. Inspect the approved intersection contract and all relevant HTTP/service callsites. First add a synthetic RED regression for an active user with membership and no global roles; then make the smallest server-side correction so list/dashboard and related reads fail closed. Preserve existing `authorize(roles=[])` denial, intersection, endpoint contracts, and all unrelated work. Do not infer semantics for `actor_roles=None`; report affected callsites and stop if a policy choice is required. Use only the listed files, run only the listed checks, report exact evidence and request independent review; do not self-approve or commit.”

## Definition of Done
- Synthetic RED/GREEN and all assigned checks have exact evidence and exit codes.
- Scope, role-intersection semantics, and service-callsite audit are documented.
- OpenCode verification and independent Hermes Reviewer assessment are recorded; no unresolved P1/P2 finding is called complete.
- Coordinator appends observed routing/evidence to `.team/ledger.md`.
- Coordinator evidence: `.team/tasks/CHPMIS-017-F3-coordinator-evidence.md`.

## Hermes card closing contract
ROLE: worker (implementation). Work only in the assigned repository workspace. Follow this pack and keep tasks serialized. Post progress with `kanban_comment`. Finish by calling exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include changed files, exact commands/results/exits, requirement trace and unresolved limits. Do not commit.
