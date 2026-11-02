ROLE: reviewer (independent, read-only)

Task ID: CHPMIS-012-F1-R2-R3-REV. Independently review the final CHPMIS-012-F1 implementation after Worker run 110 and follow-ups R2 run 112 and R3 run 113. R1 card `t_bba958db` approved the initial implementation but did not identify two transaction issues; do not inherit that verdict. Read the original F1 pack, R2/R3 packs, route design/plan, F1/R2 Worker reports (including appended corrections), the R1 review, and `.team/ledger.md`.

Review the final scoped diff in:
- `backend/app/auth/oidc.py`
- Only the F1 `/login` and `/callback` cookie integration in `backend/app/auth/routes.py`; ignore unrelated pre-existing role changes in that file.
- `backend/app/auth/models.py`
- `backend/alembic/versions/0007_oidc_pkce_browser_binding.py`
- F1/R2/R3 changes in `backend/tests/test_auth_oidc.py`
- F1 migration-head/preservation changes in `backend/tests/test_postgresql.py`
- `.team/tasks/CHPMIS-012-F1-worker-report.md`
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md`

The repository has unrelated pre-existing dirty work. Do not alter, stage, reset, restore, format, or attribute unrelated files. Do not run tests or external services; use the recorded verification evidence. Focus independently on: conditional atomic delete and affected-row handling when two callbacks loaded the same valid state; no token exchange by a losing claim; transaction retention on missing/mismatched browser binding; cookie deletion after successful consumption on every downstream HTTP/unexpected error path while retaining it on pre-consumption failures; verifier secrecy/propagation and positive token-form-body assertion; fixed callback URI; constant-time binding check; session/CSRF preservation; additive nullable migration compatibility; test validity and exact task scope. Treat test reports as evidence to audit, not as proof of correctness.

Write `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md` with Task ID, Reviewer role, reviewed scope, requirement trace, cited file/line evidence, P1/P2/P3 findings (each with priority and correction direction), explicit `Declined to judge` items, and a clear verdict `APPROVED` or `CHANGES_REQUESTED`. PostgreSQL live runtime remains NOT_VERIFIED, and live IdP/browser E2E is outside F1.

Finish with exactly one Hermes lifecycle action: `kanban_complete(result=...)` for an approved read-only review or `kanban_request_changes(reason=...)` for required fixes. Do not change implementation or run checks.
