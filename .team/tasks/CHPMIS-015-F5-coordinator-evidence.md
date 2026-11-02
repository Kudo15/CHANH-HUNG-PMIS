# CHPMIS-015-F5 Coordinator Evidence

- **Task ID:** CHPMIS-015-F5
- **Role:** Coordinator
- **Scope:** Approval gate, worker/reviewer coordination, final candidate checks, and evidence; no product-code edits.
- **DoD:** Legacy display-value rows cannot establish requester or approver decision-time authority; canonical HG2 still works; bootstrap legacy detection remains; independent review and verification are recorded.
- **Requirement trace:** mission §4B; `.team/tasks/CHPMIS-015-F5-canonical-decision-authority.md`.

## Authorization and implementation

- Automatic approval review rejected the original Worker launch twice because it did not see direct trusted authorization for the authorization-policy change. No Worker ran and no F5 product code changed during those attempts.
- The user then replied directly: **“Approve exact F5 scope.”** The approved scope is only `backend/app/auth/routes.py` and `backend/tests/test_auth_remediation.py`; decision-time checks now accept only canonical `system_admin`, while target duplicate and bootstrap legacy detection remain unchanged.
- Worker card `t_779b041f`, session `20261101_221759_5c1d85`, requested review. Worker report: `.team/tasks/CHPMIS-015-F5-worker-report.md`.
- Independent Hermes Reviewer card `t_32dc23d1`, session `20261101_222749_b9fcba`: **APPROVED, 0 P1/P2/P3**. It confirmed requester/approver canonical checks, denied legacy-only cases with no request/target/session side effects, canonical HG2 success, preserved bootstrap/duplicate detection, and no scope creep.

## Coordinator verification

All tests were run from `backend/` with `TEST_DATABASE_URL` and `DATABASE_URL` set only in-process to the synthetic loopback PostgreSQL URL.

| Command | Result |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py -k legacy_role` | Exit 0; 4 passed, 8 deselected, 1 warning. |
| `.venv\Scripts\python.exe -m pytest -q tests/test_auth_remediation.py` | Exit 0; 12 passed, 1 warning. |
| `.venv\Scripts\python.exe -m pytest -q` | Exit 0; **149 passed, 0 skipped, 6 warnings**. All four PostgreSQL tests ran against the live synthetic service. |
| `.venv\Scripts\ruff.exe check . ..\dev` | Exit 0; all checks passed. |
| `.venv\Scripts\ruff.exe format --check .` | Exit 0; 36 files already formatted. |
| `git diff --check HEAD` | Exit 0; clean. |
| `docker compose config --quiet` with the six CI synthetic values in-process | Exit 0. |

Worker's earlier full-suite run without the PostgreSQL URL was 145 passed/4 skipped; it explicitly did not claim those skips as PostgreSQL evidence. The coordinator integrated run above resolved the skip gap.

## OpenCode status

The F1 OpenCode verifier attempt ended without a verifier result and remains NOT_VERIFIED. The F5 OpenCode default-route run `2026-11-01T15-51-06-verifier-chpmis-015-f5-read-only-verification-13c1` created GUI-visible session `ses_e683150e7ffe5lbkvuUe7D3oW4` but was blocked by shell permission denial before checks. On 2026-11-02, owner authorized one F5-only DeepSeek verifier attempt. Run `2026-11-02T01-17-36-verifier-chpmis-015-f5-authorized-deepseek-verifi-7780`, session `ses_e662aace7ffe7M6ni63Qu0NfHo`, used `deepseek/deepseek-flash` and again received shell permission denial on all six assigned checks; only unassigned `git status --short` ran (exit 0). The role completed as `blocked`; OpenCode process exit 0 is not check evidence and the helper exited 1. Static inspection is noted only as static evidence; tests, Ruff, scoped diff, and PostgreSQL behavior remain NOT_VERIFIED for that run. No permissions/settings were changed, no further retry is authorized. Full run metadata and exact limits: `.team/tasks/CHPMIS-015-F5-opencode-readonly-checks.md`.
