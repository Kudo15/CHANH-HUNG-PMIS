ROLE: reviewer (independent, read-only)

Task ID: CHPMIS-012-F1

Read the complete approved task pack `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`, design/plan, and Worker report `.team/tasks/CHPMIS-012-F1-worker-report.md`. Review the current implementation in the shared repository. The Worker run is `t_54dd05f6` / run 110 and is in review.

Scope to review:
- `backend/app/auth/oidc.py`
- The F1-only `/login` and `/callback` cookie glue in `backend/app/auth/routes.py`
- `backend/app/auth/models.py`
- `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`
- F1 regressions in `backend/tests/test_auth_oidc.py`
- F1 migration-head and preservation regression in `backend/tests/test_postgresql.py`
- `.team/tasks/CHPMIS-012-F1-worker-report.md`

The repository was already dirty before F1. In particular, `backend/app/auth/routes.py`, `backend/tests/test_postgresql.py`, and migration `0006_bootstrap_trust_boundary.py` contain pre-existing unrelated work. Use the task pack, Worker report and prior task/ledger notes to distinguish F1 additions from that pre-existing work. Do not attribute, alter, stage, reset, restore, format, or otherwise mutate any file. Do not run tests or external services.

Review browser-bound S256 PKCE, verifier secrecy and propagation, random binding token storage-by-digest, constant-time comparison, fixed callback URI, missing/mismatched/legacy/expired/replay behavior, non-consumption of Browser A state after Browser B fails, atomic one-time consumption before token exchange, route cookie attributes and clearing, signed-token/session/CSRF preservation, additive nullable migration compatibility, acceptance coverage, and exact scope.

Write the review result to `.team/tasks/CHPMIS-012-F1-independent-review.md`. Include Task ID, Reviewer role, scope, requirement trace, cited files/lines, P1/P2/P3 findings, `Declined to judge` behaviors (or explicitly `None`), and a clear verdict `APPROVED` or `CHANGES_REQUESTED`. Do not change implementation. If a material issue exists, request changes; do not self-approve or close the platform gate.

Finish through exactly one Hermes lifecycle action: `kanban_complete(result=...)` for an approved read-only review, or the appropriate review-change action if findings require changes. Do not edit product code.
