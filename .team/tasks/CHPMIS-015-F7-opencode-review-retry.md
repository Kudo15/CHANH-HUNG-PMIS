# CHPMIS-015-F7 — OpenCode Final Review Retry

Read-only independent verifier. Do not edit, stage, commit, or run tests. Do not inspect environment values, credentials, or Docker configuration.

Read `AGENTS.md`, `.team/CHARTER.md`, `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`, `.team/tasks/CHPMIS-015-F7-codex-worker.md`, and `.team/tasks/CHPMIS-015-F7-reproduction-diagnosis.md`. In the main repository workspace, inspect only the F7 code at `backend/app/auth/routes.py` around line 391 and the F7 PostgreSQL test around lines 669-865. These source edits are uncommitted; do not use the claim-created Hermes worktree as the code source. Pre-existing unrelated changes in those two files must remain untouched.

Check: target User row is locked before existing-role lookup inside the same transaction; existing approval checks and effects remain. Test namespace starts `chpmis_015_f6_`; test asserts one 200/one 409, one active canonical role, one approved/one pending, and session revocation. Pay particular attention to the test's `before_cursor_execute` barrier: it catches `BrokenBarrierError`. Decide whether this can let the test pass without both competing transactions reaching the intended race point; if so, request a concrete correction. Do not assume coordinator test output proves test determinism.

Coordinator evidence: focused PostgreSQL case 1 passed/5 deselected; PostgreSQL module 6 passed; backend suite 159 passed; Ruff checks and scoped diff check passed. Hermes independent reviewer approved with 0 P1/P2/P3 findings. This review must provide a concise final verdict and any `file:line` findings, or state that it could not complete. Do not use tools outside the read-only source inspection needed for this verdict.
