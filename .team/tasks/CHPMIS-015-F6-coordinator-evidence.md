# CHPMIS-015-F6 — Coordinator Evidence and Corrections

- **Task ID:** CHPMIS-015-F6
- **Role:** Coordinator
- **Status:** BLOCKED — live PostgreSQL reproduction is confirmed; product fix requires a separate Human Gate approval.
- **Requirement trace:** Mission §6; `.team/tasks/CHPMIS-015-F6-distinct-request-same-target-pg-repro.md`.
- **Worker:** Hermes card `t_9a17eb5a`, session `20261101_223615_566dda`.
- **Independent Reviewer:** Hermes card `t_5338365e`, session `20261101_224355_e9c433`, APPROVED (0 P1/P2/P3).

## Scope and source files

Worker changed only `backend/tests/test_postgresql.py` and added `.team/tasks/CHPMIS-015-F6-worker-report.md`. No application, model, migration, schema, or authorization files changed. The existing same-request test remains unchanged.

## Live PostgreSQL evidence

Worker reported the following from the synthetic PostgreSQL service:

- `pytest -q tests/test_postgresql.py -k distinct_requests_same_target`: exit 1; actual result contained two HTTP 200 approvals for different request IDs to one target.
- `pytest -q tests/test_postgresql.py`: exit 1; 4 existing PostgreSQL tests passed and the new distinct-request case failed. The existing same-request concurrency test passed.
- Without `TEST_DATABASE_URL`, the PostgreSQL module reported 5 skipped, exit 0; this is not PostgreSQL acceptance evidence.
- Ruff check, Ruff format check, and scoped `git diff --check` exited 0.

The test asserts the expected status distribution before its later role-count assertion. Therefore that focused failure alone establishes two successful approvals, but it does not reach the test's `len(roles)` check. The Coordinator independently queried the preserved synthetic test databases read-only and confirmed the database side effects:

| Database | Synthetic target | Active canonical roles | Approved requests | Revoked target sessions |
|---|---|---:|---:|---:|
| `chpmis_013_distinct_target_11ad7240` | `syn_dist_9514010b_tgt` | 2 | 2 | 1 |
| `chpmis_013_distinct_target_b76f92c6` | `syn_dist_1448fb48_tgt` | 2 | 2 | 1 |
| `chpmis_013_distinct_target_ce915ae6` | `syn_dist_a3bf913a_tgt` | 2 | 2 | 1 |
| `chpmis_013_distinct_target_ffb1ad87` | `syn_dist_059076a8_tgt` | 2 | 2 | 1 |

Coordinator query result: exit 0. It read only `users`, `user_roles`, `system_admin_requests`, and `sessions` rows matching these synthetic target IDs. It performed no writes; all four databases remain preserved.

## Evidence corrections and review limits

- The Worker report names `chpmis_013_distinct_target_1448fb48` and `..._9514010b`, but those suffixes are target IDs, not the actual database names. The actual names and row counts are listed above.
- The task pack required a RED reproduction before any file edit. The reported pre-addition pytest command exited 5 with 4 deselected, which is a no-test baseline, not a RED reproduction. The deterministic test was added before the live RED run. The live RED output is valid defect evidence; the required ordering is **NOT VERIFIED / not followed**.
- The database helper currently emits a `chpmis_013_` prefix. The test name includes `distinct_target` and a random suffix, but it does not identify the F6 task in the database prefix. This is a reporting/isolation-label deviation; every observed database was unique and preserved.
- Reviewer R1 approved the test and independently reran the RED case. Its review record's assertions that the pre-addition command satisfied the RED-before-edit requirement and that the recorded suffixes were database names are inaccurate; this Coordinator record supersedes those two claims. The review did read and assess the test diff, barrier, expected contract, live failure, and same-request test.

## Finding and gate

Two distinct pending `grant` requests against one target can both return 200 and commit two canonical `system_admin` rows. Both requests are recorded approved and the target session is revoked. The same-request 200/409 control still passes. This confirms a concurrency defect in the approved workflow transaction.

No product fix is authorized by the F5 approval. A proposed no-schema correction is prepared in `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`; it must remain undispatched until the owner explicitly approves that exact scope. Do not add a unique constraint or migration under this proposal.
