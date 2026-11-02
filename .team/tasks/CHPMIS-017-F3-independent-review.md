# CHPMIS-017-F3 — Independent Reviewer Pack

ROLE: reviewer (read-only). Inspect the implementation and evidence; do not modify source, tests, reports, task packs, or ledger.

## Task identity
- **Task ID:** CHPMIS-017-F3-R1
- **Role:** Hermes Reviewer, read-only
- **Implementation card:** `t_e4f5224f`
- **Trace:** mission §4A; `.team/tasks/CHPMIS-017-F3-empty-global-roles.md`; approved CHPMIS-017 role-intersection contract.
- **Status:** READY FOR REVIEW. OpenCode Tester timed out; its independent test verdict is `NOT_VERIFIED` and must not be represented as PASS.

## Objective
Independently inspect the full scoped CHPMIS-017-F3 diff and relevant existing callers/tests. Decide whether the empty-global-role correction is minimal, fail-closed, consistent across list/dashboard and related HTTP endpoints, preserves intersection and `actor_roles=None` semantics, and meets the assigned acceptance criteria. Do not edit implementation, reports, or ledger.

## Review scope
Read the full diff and these sources as relevant: `backend/app/projects/routes.py`, `backend/app/projects/service.py`, `backend/app/auth/policy.py`, `backend/tests/test_projects.py`, `backend/tests/test_dashboard_audit.py`, `backend/tests/test_tasks_workflow.py`, the F3 task pack and Worker report. Confirm changed files are within the F3 allowlist. Treat Worker test claims as unverified unless independently evidenced in the checkout/task records; OpenCode run `2026-11-01T14-18-59-verifier-chpmis-017-f3-independent-verifier-7eaf` timed out before producing a result.

## Required review criteria
- Empty global roles with a valid session and project membership reveal no list/dashboard rows or counts.
- Revocation of the last global role while membership remains does not restore business access.
- Detail/member/task/audit endpoints remain consistently denied under empty roles; no UI-only control, fake context policy copy, permission union, or role expansion.
- Existing `authorize(roles=[])` denial, unknown-role handling, and multi-role intersection behavior remain intact.
- `actor_roles=None` callsites and existing semantics are accurately traced; no newly introduced bypass.
- Tests assert meaningful outcomes and use synthetic data; no unsupported test pass or scope claim.
- Report each finding as `file:line`, P1/P2/P3 with correction direction; conclude `APPROVED` or `CHANGES_REQUESTED`.

## Boundaries and closeout
Read-only. No edits, shell commands that mutate, commits, or additional test runs. Use a separate clean Hermes card/session and the existing project workspace. Finish with `kanban_complete(result=verdict and findings)` or `kanban_block(reason=...)`. A review approval does not waive the timed-out OpenCode Tester gate.
