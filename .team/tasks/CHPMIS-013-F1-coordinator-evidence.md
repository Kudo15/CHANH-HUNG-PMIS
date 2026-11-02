# CHPMIS-013-F1 Coordinator Evidence

- **Task ID:** CHPMIS-013-F1
- **Role:** Coordinator
- **Scope:** PostgreSQL runtime setup, independent verification, task evidence, and ledger; no product-code edits.
- **DoD:** F1 acceptance commands pass against live synthetic PostgreSQL; schema/data preservation evidence recorded; independent read-only verification and separate review complete.
- **Requirement trace:** mission §3 Priority 1; `.team/tasks/CHPMIS-013-F1-current-head-schema-gate.md`.

## Runtime and preservation

- Service: existing task-specific container `chpmis-gate-20261101-db-1`, PostgreSQL **17.11 (Debian 17.11-1)**, loopback-only port 5432; state `running` at evidence capture.
- Worker and both independent verification passes created fresh UUID-suffixed databases with `chpmis_013_` prefixes. All were preserved; no database or volume was dropped or reset.
- PostgreSQL listed 52 preserved F1 synthetic databases across the three verification passes:
  - `chpmis_013_concurrent_appr_2feadb37`, `..._368a1dcb`, `..._422b5086`, `..._4a10465a`, `..._53fe1993`, `..._5a8e9ef7`, `..._7aeada09`, `..._9507272a`, `..._a7465a68`, `..._ae94391c`, `..._b028fec6`, `..._e741e325`, `..._eeaea56c`.
  - `chpmis_013_empty_to_head_196a70d3`, `..._20e987ea`, `..._363bdf52`, `..._3dc7626c`, `..._56c07246`, `..._5b5da388`, `..._622ecc8f`, `..._6aa8b3a4`, `..._726509ed`, `..._7be94958`, `..._9ccdd131`, `..._c692ba2e`, `..._e3530137`.
  - `chpmis_013_pop_0005_head_398d86cb`, `..._40cda274`, `..._5654ff54`, `..._65c6d615`, `..._67cd0c1c`, `..._6bbb9f04`, `..._9a0a48e4`, `..._a63c086f`, `..._b7cab483`, `..._c911a8d3`, `..._d80fe8a5`, `..._e793ca23`, `..._f3e682af`.
  - `chpmis_013_receipt_trigger_06b955c9`, `..._45422f02`, `..._6f548b3a`, `..._849ce35d`, `..._878eb4c2`, `..._9395e071`, `..._a1d5a844`, `..._a6cc0c82`, `..._b1f095c1`, `..._c1481b00`, `..._cdffd9ca`, `..._eb38ff86`, `..._f49f91a2`.
- Test contract starts with a new database containing zero tables or, for the populated path, revision `0005_initial_admin_bootstrap`; each live migration test ends at `0006_bootstrap_trust_boundary` with 12 expected tables. The populated-path test confirms synthetic user, receipt, and role rows survive and the new receipt metadata columns initialize to `NULL`.
- Trigger test confirms PostgreSQL rejects both receipt `UPDATE` and `DELETE` with `admin_bootstrap_receipts rows are immutable`, and the original row remains intact.
- Schema inventory: unique and foreign-key constraints are asserted. The reviewer confirmed the approved schema contains **zero CHECK constraints**; none were invented.

## Coordinator verification

All commands were run from `backend/`; `TEST_DATABASE_URL` and `DATABASE_URL` were set only in-process to the synthetic loopback URL.

After the F5 changes, the final integrated command `.venv\Scripts\python.exe -m pytest -q` was rerun against the same synthetic loopback service and completed with **149 passed, 0 skipped, 6 warnings, exit 0**. This includes all four live PostgreSQL tests plus the new F5 regressions.

| Command | Result |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` | Exit 0; 4 passed, 0 skipped, 7 warnings. |
| `.venv\Scripts\python.exe -m pytest -q` | Restricted run: exit 1, 129 passed and 16 temporary-directory permission errors. Re-run under reviewed execution: exit 0; 145 passed, 0 skipped, 6 warnings. |
| `.venv\Scripts\ruff.exe check . ..\dev` | Exit 0; All checks passed. |
| `.venv\Scripts\ruff.exe format --check .` | Exit 0 under reviewed execution; 36 files already formatted. |
| `.venv\Scripts\python.exe -m alembic upgrade head --sql` | Exit 0; offline SQL generated through revision 0006 (supplemental only). |
| `docker compose config --quiet` with six CI-only synthetic values in-process | Exit 0. |
| `git diff --check HEAD -- backend/` | Exit 0. |
| `git diff --check HEAD` | Initially exit 2 from trailing whitespace in the coordinator's earlier F3 ledger line; that line was corrected, then the whole diff check exited 0. |

Non-elevated attempts of the full suite and Ruff format were denied access to the pre-existing `backend/.pytest-temp` directory. No files in that directory were read, edited, or removed. The exact required commands passed under reviewed execution.

## Independent review and OpenCode verification

- Hermes Reviewer: card `t_01953436`, session `20261101_220807_dd8e1b`, **APPROVED**, 0 P1/P2/P3. Reviewer independently ran live PostgreSQL tests (4 passed, 0 skipped), full backend suite (145 passed, 0 skipped), Ruff check/format, offline Alembic SQL, Compose config, and scoped diff check. Reviewer also confirmed PostgreSQL 17.11, 52 task-prefixed databases preserved, and zero current-schema check constraints.
- OpenCode read-only verifier: run `2026-11-01T15:05:12.684Z-verifier-chpmis-013-f1-read-only-gate-verificatio-f90f` remained without a verifier result for approximately ten minutes; final role-run ledger metadata records status `failed`, session `ses_e685b5734ffeai6y5jaJnR7zg0`, and GUI listed. The exact CLI process was then cancelled; driver exited 1 (`opencode exited 4294967295`). No session export or raw logs were read. This is NOT_VERIFIED, so F1 remains in review.

## Dispatch deviation

The Hermes helper used a generic queue dispatch and started the old, already-completed CHPMIS-017-F3 Worker card `t_e4f5224f` instead of the new F1 Reviewer card. Its process was immediately terminated and the card claim reclaimed; the card is now in `review`, and its prior completed implementation/review remains intact. The accidental run made no product-file changes. F1 Reviewer `t_01953436` was then claimed and run by exact task ID.
