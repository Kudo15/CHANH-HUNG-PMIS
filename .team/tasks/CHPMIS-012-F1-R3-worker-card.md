ROLE: worker (test-only correction)
Work only in the existing approved repository workspace. Read `AGENTS.md`, `.team/CHARTER.md`, the original F1 pack, R2 pack, this R3 pack, the R2 Worker report, and `.team/ledger.md` before editing. Preserve all dirty files.

Task ID: CHPMIS-012-F1-R3. This task follows R2 run 112. The R2 atomic conditional claim and route cookie cleanup code should remain untouched. The positive `DefaultOIDCClient` supplied-verifier body assertion is required and must remain. Remove only the optional `code_verifier=None` omission subcase; do not change `DefaultOIDCClient`, imports needed by the positive test, or other tests. Append a correction section to `.team/tasks/CHPMIS-012-F1-R2-worker-report.md` (do not rewrite existing evidence) recording the exact R2 command/CWD deviations and the coordinator's exact root `git diff --check` pass after normalizing the coordinator-owned ledger line ending. Keep the scope to these two files.

Use the real prompts.chat Feature coding template by Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved via `.agents/skills/prompt-lookup` and cited in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`. Modernization: make only the test-scope correction, preserve code and dirty work, run exactly the listed R3 checks in their listed CWDs, and report every command/CWD/output/exit code separately.

Verification from `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`; `.venv\Scripts\ruff.exe check . ../dev`; `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py tests/test_auth_oidc.py`. From repo root: `git diff --check`. No other command variants, no mutating formatters, no environment inspection. Do not stage/commit/push/deploy or run Git discard commands. If any check fails, report it without repairing outside the two-file allowlist.

Finish with exactly one Hermes lifecycle action: `kanban_request_review(summary=...)` when the cleanup is complete, or `kanban_block(reason=...)` if unable to proceed. Do not claim F1 complete.
--- REQUIREMENT ---
Read `.team/tasks/CHPMIS-012-F1-R3-test-scope-cleanup.md` as authoritative.
