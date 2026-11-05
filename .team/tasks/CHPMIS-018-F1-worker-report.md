# CHPMIS-018-F1 Worker Report — Concurrent Task Status Lost Update (PostgreSQL)

- **Task ID:** CHPMIS-018-F1
- **Role:** PostgreSQL Test Worker (test-only)
- **Date:** 2026-11-03
- **Status:** RED REPRODUCED — lost update confirmed on live synthetic PostgreSQL; test-only diff complete; awaiting independent Tester/Reviewer.
- **Trace:** mission §6 (task lost-update reproduction); approved Human Gate 3 transition graph (`in_progress -> done` and `in_progress -> cancelled` both allowed for PM); existing CHPMIS-018 task consistency finding.
- **Prompt template:** prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa` (retrieved via installed prompt-lookup in the task pack), modernized to this test-only PostgreSQL scope.

## 1. Result

**RED: both concurrent PM transitions from the same `in_progress` prior state were accepted (HTTP 200 + 200), both `task:transition` audit events recorded the stale `before.status = in_progress`, and the final task row kept only the last commit's status.** The `in_progress -> done` transition is lost. No product fix is made in this task; the defect stays blocked for a separately scoped Human Gate review (row lock / optimistic concurrency).

Observed final state in the preserved test database (read-only re-query):
- Final task status: `done` (the last-committed winner's target; `cancelled` was overwritten).
- Audit `task:transition` rows: exactly 2, both with `before_values.status = in_progress`:
  - actor `..._pm2`: `before={'status': 'in_progress'} after={'status': 'cancelled'}`
  - actor `..._pm1`: `before={'status': 'in_progress'} after={'status': 'done'}`

## 2. Scope compliance

- Modified **only** `backend/tests/test_postgresql.py` (purely additive: 300 insertions, 0 deletions per `git diff --stat`).
- This report file is the only other changed path.
- No changes to `backend/app/`, models, migrations, schema, permission rules, transition graph, API responses, or workflow behavior. No product fix implemented.
- Existing same-request admin-approval concurrency test `test_postgresql_concurrent_approval_serialized` preserved byte-for-byte (diff is insertions only).
- All synthetic databases preserved; no `DROP`/reset/cleanup executed.

## 3. Synthetic PostgreSQL context

- Service: existing loopback-only container `chpmis-gate-20261101-db-1` (postgres:17-bookworm, 17.11), published at `127.0.0.1:5432`. No new service was started.
- Process-local settings (set only for the test process, never printed into any report body): `TEST_DATABASE_URL` and `DATABASE_URL` = `postgresql+psycopg://pmis_test:***@127.0.0.1:5432/pmis_test`.
- Fresh migrated databases created in the `018_f1` namespace (all preserved):
  - Scratch harness (pre-file-change live reproduction): `018_f1_95cfd4bc`, `018_f1_9de373df`, `018_f1_5afccd2f`.
  - In-file test runs: `018_f1_conc_task_trans_e9623358`, `018_f1_conc_task_trans_f6ee8aeb`, `018_f1_conc_task_trans_61ac7020` (final focused run).
- Seeded per run: 2 synthetic `project_manager` users, 1 project, 2 explicit `project_manager` memberships, 1 task seeded at `in_progress`, 2 sessions, 1 seed audit event (`task:seed`) so the `task:transition` count is unambiguous.

## 4. Deterministic reproduction technique

`_TaskTransitionRaceGate` in `backend/tests/test_postgresql.py` uses a bounded SQLAlchemy event barrier (no timer-only race):

1. **Stage 1 (task SELECT gate):** `before_cursor_execute` listener matches the request's `SELECT ... FROM tasks` (by task id in parameters). Each of the two request connections hits a one-shot `threading.Barrier(2, timeout=10.0)`; neither passes its SELECT until both requests have arrived. If the second request never arrives, the barrier times out and the test fails loudly (no false pass).
2. **Stage 2 (UPDATE gate):** `after_cursor_execute` records when each connection's task SELECT completes; `before_cursor_execute` additionally blocks any `UPDATE tasks` for the target task until **both** SELECTs have completed, so both requests provably read the same prior state before either writes.
3. Listeners are attached at the `sqlalchemy.engine.Engine` **class** level so they cover both the app engine (created inside the `TestClient` lifespan) and the seed/verify engine, and are removed in `finally` (best-effort `event.remove` with guard).
4. Verified gate observables before the RED assertion: `len(select_connections) == 2`, `len(select_completed) == 2`, `update_gate_waiters == 2`.

## 5. Verification (exact commands, outputs, exits)

All commands run from `backend/` with the process-local `TEST_DATABASE_URL`/`DATABASE_URL` above. The environment variable values are intentionally not reproduced here (credential hygiene); only presence was required.

### 5.1 Step 1 — live reproduction before any file change (scratch harness, temporary test process)

- **Command:** `powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\ANHVU\AppData\Local\Temp\opencode\chpmis018_f1_scratch.ps1` (runs `backend\.venv\Scripts\python.exe C:\Users\ANHVU\AppData\Local\Temp\opencode\chpmis018_f1_scratch.py` with the same process-local env; cwd `backend/`).
- **Final scratch run (v3 harness, DB `018_f1_5afccd2f`), exit code 3 (lost-update verdict), key output:**
  ```
  scratch_db_name=018_f1_5afccd2f
  tables_before_migration=[]
  revision=0007_oidc_pkce_browser_binding
  table_count=12
  select_connections_seen=2
  selects_completed=2
  update_gate_waiters=2
  result target=cancelled http=200 ... "status": "cancelled"
  result target=done http=200 ... "status": "cancelled"
  final_task_status=cancelled
  transition_audit_count=2
  audit_row actor=scr018f1_bc9b6e68_pm2 before={'status': 'in_progress'} after={'status': 'cancelled'}
  audit_row actor=scr018f1_bc9b6e68_pm1 before={'status': 'in_progress'} after={'status': 'done'}
  VERDICT=LOST_UPDATE_BOTH_ACCEPTED_STALE_BEFORE
  SCRATCH_EXIT=3
  ```
- Earlier scratch runs (`018_f1_95cfd4bc` with a single-select barrier; `018_f1_9de373df` with the final two-stage gate) reached the same verdict: both 200, both stale `in_progress` before-values.

### 5.2 Focused test (assigned verification)

- **Command:** `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k concurrent_task_transition_serialized`
- **Exit code:** 1 (expected RED — the lost-update gate assertion fails)
- **Output (final file state):**
  ```
  F                                                                        [100%]
  =================================== FAILURES ===================================
  ______________ test_postgresql_concurrent_task_transition_serialized ____________

  ...
  >           assert sorted(code for _, code, _ in results) == [200, 400], (
                  "Lost update: both concurrent in_progress transitions were accepted. "
                  f"Expected one 200 and one 400 invalid-transition, observed: {actual}"
              )
  E           AssertionError: Lost update: both concurrent in_progress transitions were accepted. Expected one 200 and one 400 invalid-transition, observed: [('cancelled', 200, {'id': 'syn_018f1_5afe4517_task', ..., 'status': 'done', ...}), ('done', 200, {'id': 'syn_018f1_5afe4517_task', ..., 'status': 'done', ...})]
  E           assert [200, 200] == [200, 400]
  E
  E            At index 1 diff: 200 != 400
  E            Use -v to get more diff

  tests\test_postgresql.py:1116: AssertionError
  =========================== short test summary info ============================
  FAILED tests/test_postgresql.py::test_postgresql_concurrent_task_transition_serialized
  1 failed, 6 deselected, 2 warnings in 8.52s
  ```
- **Skip status:** 0 skipped — the test executed against live PostgreSQL (not skipped).

### 5.3 Module regression (unchanged existing tests still pass)

- **Command:** `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
- **Exit code:** 1 (sole failure is the new RED reproduction test)
- **Output:**
  ```
  ......F                                                                  [100%]
  =========================== short test summary info ============================
  FAILED tests/test_postgresql.py::test_postgresql_concurrent_task_transition_serialized
  1 failed, 6 passed, 10 warnings in 28.87s
  ```
- The 6 existing tests — including the preserved same-request admin-approval concurrency test `test_postgresql_concurrent_approval_serialized` — passed.

### 5.4 Lint / format

- **Command:** `.venv\Scripts\ruff.exe check tests/test_postgresql.py` → `All checks passed!`, exit 0.
- **Command:** `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py` → `1 file already formatted`, exit 0.

### 5.5 Whitespace check

- **Command (repo root):** `git diff --check -- backend/tests/test_postgresql.py .team/tasks/CHPMIS-018-F1-worker-report.md` → empty output, exit 0.
- Note: the report file is untracked, so `git diff --check` covers only the tracked test file; the report was additionally hand-checked for trailing whitespace/EOF.

## 6. Preservation evidence

- Read-only enumeration (no drop/reset) after the final run:
  ```
  018_f1_databases_preserved=['018_f1_5afccd2f', '018_f1_95cfd4bc', '018_f1_9de373df', '018_f1_conc_task_trans_61ac7020', '018_f1_conc_task_trans_e9623358', '018_f1_conc_task_trans_f6ee8aeb']
  ```
- Final focused-run database `018_f1_conc_task_trans_61ac7020` re-queried read-only:
  ```
  task_row={'id': 'syn_018f1_5afe4517_task', 'status': 'done', 'updated_at': 2026-11-03 01:22:37.917779+00:00}
  audit_row_count=3
  audit_row actor=syn_018f1_5afe4517_pm1 action=task:seed before=None after=None at=2026-11-03 01:22:37.692378+00:00
  audit_row actor=syn_018f1_5afe4517_pm2 action=task:transition before={'status': 'in_progress'} after={'status': 'cancelled'} at=2026-11-03 01:22:37.916570+00:00
  audit_row actor=syn_018f1_5afe4517_pm1 action=task:transition before={'status': 'in_progress'} after={'status': 'done'} at=2026-11-03 01:22:37.917801+00:00
  row_counts={'users': 2, 'sessions': 2, 'tasks': 1, 'audit_events': 3, 'projects': 1, 'project_members': 2}
  ```

## 7. Defect characterization (reproduction only — no fix)

- `transition_task_status` (`backend/app/projects/service.py`) reads the task with a plain `SELECT`, validates the transition against the stale `task.status`, then commits `UPDATE tasks` + audit INSERT with no row lock and no optimistic-concurrency check. Under READ COMMITTED the two concurrent transactions each read `in_progress`, each passes the graph check, and both commit; the second commit silently overwrites the first (lost update) and the audit trail contains two events with the same stale before-state.
- Any fix (e.g. `SELECT ... FOR UPDATE` on the task row, conditional `UPDATE ... WHERE status = :old`, or an optimistic version column) is **out of scope** here and requires a separately scoped Human Gate review. This task stops at RED evidence.

## 8. Limits and open items

- Reproduction uses the in-process `TestClient` + a 2-thread pool (deterministic barrier), not two separate OS processes; this is the same harness shape as the existing preserved concurrency tests in the file.
- The lost update was reproduced 6 times total: 3 scratch-harness runs (`018_f1_95cfd4bc`, `018_f1_9de373df`, `018_f1_5afccd2f`) and 3 in-file test runs (`018_f1_conc_task_trans_e9623358` first focused, `018_f1_conc_task_trans_f6ee8aeb` module regression, `018_f1_conc_task_trans_61ac7020` final focused); each run used a fresh preserved database and every run observed both HTTP 200 with stale `in_progress` before-values.
- Independent Tester rerun and independent Reviewer of the test-only diff are still required; do not mark this task complete before that review.
- No commit was made; all changes remain in the working tree.
- **RED-only nature of the two-stage barrier (Reviewer finding P2-1):** The Stage 2 gate assertion `update_gate_waiters == 2` — both requests holding the stale prior read before either writes — is specific to reproducing the current lost update. This deterministic barrier test is **not expected to pass after a row-lock fix**: the second task SELECT may block on the row lock held by the first transaction before both SELECTs can pass the barrier, so the test would never reach its green path under the fixed code. It must therefore be treated as a **RED reproducer of the current defect, not a green regression test for a future fix**; any regression test matching a future fix is out of scope here and belongs to the separately scoped row-lock / optimistic-concurrency Human Gate task (§7).
