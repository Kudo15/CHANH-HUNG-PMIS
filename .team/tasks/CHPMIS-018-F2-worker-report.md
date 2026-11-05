# CHPMIS-018-F2 Worker Report — Serialized Task Status Decisions (PostgreSQL row lock)

- **Task ID:** CHPMIS-018-F2
- **Role:** OpenCode Worker (bounded Python/FastAPI/SQLAlchemy scope)
- **Date:** 2026-11-03
- **Status:** GREEN — owner-approved serialized behavior implemented and live-verified on synthetic PostgreSQL; awaiting independent OpenCode Tester and Reviewer.
- **Trace:** mission §6 (task lost-update defect); CHPMIS-018-F1 (RED reproduction, owner-accepted starting evidence); approved local task transition graph HG3; `.team/tasks/CHPMIS-018-F2-task-transition-concurrency-proposal.md` (OWNER APPROVED 2026-11-03); `.team/tasks/CHPMIS-018-F2-task-transition-worker.md`.
- **Prompt template:** prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa` (https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template), retrieved via the installed `prompt-lookup` skill and modernized in the task pack. The template's generic README instruction does not expand this allowlist.

## 1. Required session start (reads performed)

Read before acting, in this order: `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, `.team/tasks/CHPMIS-018-F2-task-transition-worker.md` (this task pack), `.team/tasks/CHPMIS-018-F2-task-transition-concurrency-proposal.md`, `.team/tasks/CHPMIS-018-F1-worker-report.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, then the relevant task/workflow code: `backend/app/projects/service.py` (`transition_task_status` and audit writer), `backend/app/projects/routes.py` (status PATCH route), `backend/app/database.py` (engine/session), `backend/app/projects/models.py` (`Task`, `AuditEvent`), `backend/app/projects/schemas.py` (`TaskStatus`), `backend/app/main.py` (per-TestClient lifespan engine), `backend/app/auth/session.py`, and `backend/tests/test_postgresql.py` (F1 gate and all existing live tests).

`git status --short` was captured before edits; all pre-existing dirty/untracked work was preserved. No file outside the allowlist was modified.

## 2. Result

**GREEN: concurrent `in_progress → done` vs `in_progress → cancelled` now serialize.** Exactly one request returns 200, the other returns 400 using the existing response semantics (invalid transition, or terminal cancelled state when cancelled wins), exactly one `task:transition` audit event records the actual `before`/`after` status, and the final task status equals the winner. Verified live on synthetic PostgreSQL 17 (see §4). No schema, migration, dependency, transition graph, authorization policy, or other API behavior changed.

## 3. Implementation (product change)

`backend/app/projects/service.py` only, inside `transition_task_status`:

- After the existing access/non-disclosure checks (task 404, project 404, no-role 404, archived 400) and **before** the transition decision, the service re-reads the task row with a PostgreSQL row lock in the existing request transaction:
  `SELECT ... FROM tasks WHERE id = :id FOR UPDATE` via `select(Task).where(Task.id == task_id).with_for_update().execution_options(populate_existing=True)`.
- `populate_existing=True` is required: the initial plain `SELECT` had already loaded the instance into the ORM identity map with the stale status, and without it the identity map would return the stale value even after the locked re-read (observed: with the lock but without `populate_existing`, the second request still evaluated against the stale status and both requests returned 200 — reproduced and fixed during this task).
- If the locked re-read returns no row, the existing 404 non-disclosure response is returned.
- The row lock is held until the transaction commits/rolls back, so the status `UPDATE` and the `task:transition` audit `INSERT` remain atomic with the decision. The loser then evaluates the **latest committed** status against the unchanged approved graph (`ORDINARY_TRANSITIONS` / `PM_ADDITIONAL_TRANSITIONS`) and receives the existing 400; no new conflict response was added.
- Everything downstream (terminal-state check, auditor 403, global authorization, member/PM graph evaluation, audit write, `db.commit()`, `db.refresh()`) is unchanged and now operates on the refreshed ORM state.

Diff: `backend/app/projects/service.py` — 23 insertions, 1 deletion (import line + lock block).

## 4. Lock-compatible regression test (test change, written first)

`backend/tests/test_postgresql.py` only:

- The F1 two-stage reproducer (`_TaskTransitionRaceGate`) is replaced by `_SerializedTransitionGate` in the same task-owned test `test_postgresql_concurrent_task_transition_serialized`. The F1 gate's UPDATE stage (hold both transactions with stale reads before either writes) is inherently incompatible with a row lock — the second transaction would block inside the database — and is therefore removed. The F1 RED report is preserved untouched (`.team/tasks/CHPMIS-018-F1-worker-report.md`) and remains the owner-accepted starting evidence.
- New gate (bounded synchronization, no timer-only race):
  1. **Plain task SELECT barrier:** a bounded `threading.Barrier(2, timeout=10.0)` on the `Engine`-class `before_cursor_execute` event holds each request at the first **non-locking** `SELECT ... FROM tasks` for the target task until both have arrived — both provably read the same committed `in_progress` prior state. This stage acquires no row lock, so it cannot deadlock under the fix.
  2. **Row-lock SELECT observation:** every completed `SELECT ... FROM tasks ... FOR UPDATE` for the target task is counted (`after_cursor_execute`), proving both requests went through the serialized decision path; under the fix the second lock SELECT can only complete after the first request commits.
  3. Listeners are attached at the `sqlalchemy.engine.Engine` class level (each `TestClient` context builds its own app engine in the lifespan) and removed in `finally`, matching the existing F1/admin-approval test pattern.
- Assertions (actual outcomes/state/audit, winner-agnostic): both requests observed at the barrier; `lock_selects_completed == 2`; status codes exactly `[200, 400]`; the 400 detail is one of the **existing** messages (`Invalid transition from <s> to <t>` or `Task is in terminal cancelled state` — which one depends on which target wins, so the test asserts on the union rather than a fixed winner); winner response `status` matches its target; exactly one `task:transition` audit row with `before_values.status == in_progress` and `after_values.status == <winner target>`; final `tasks.status == <winner target>`.
- The winner is not assumed: both `done`-wins and `cancelled`-wins interleavings are observed across runs (see §6), and the assertions hold in both cases.
- All other tests in the file, including both preserved admin-approval concurrency tests (`test_postgresql_concurrent_approval_serialized`, `test_postgresql_distinct_requests_same_target_concurrency`), are byte-for-byte unchanged and pass.

## 5. Verification (exact commands, outputs, exit codes)

Synthetic context: the owner-approved fresh PostgreSQL 17 container on a random loopback port with the process-generated synthetic password supplied to this process via `TEST_DATABASE_URL` / `DATABASE_URL` (presence verified; values never printed or inspected; no other services used). No container was started/stopped by this Worker, no role permissions altered, no database dropped or reset.

All commands from `backend/`:

1. **Focused regression — BEFORE product fix (RED on the new lock-compatible test):**
   `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k concurrent_task_transition_serialized` → `1 failed, 6 deselected`, **exit 1**, 0 skipped (executed live). First failure: `lock_selects_completed == 0` (service issued no `FOR UPDATE` yet). This is the honest observed pre-fix result of the new regression; it corroborates the owner-accepted F1 RED.
2. **Focused regression — AFTER product fix (GREEN):** same command → `1 passed, 6 deselected, 2 warnings in ~3s`, **exit 0**, 0 skipped. Re-run twice more for stability: **exit 0** both times.
3. **Module regression:** `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` → `7 passed, 10 warnings in 16.63s`, **exit 0**, **0 skipped** (all live, including both preserved admin-approval concurrency tests and the new serialized-transition regression).
4. **Related suites:** `.venv\Scripts\python.exe -m pytest -q tests/test_tasks_workflow.py tests/test_projects.py` → `16 passed, 1 warning in 5.83s`, **exit 0**, 0 skipped (16 collected, verified by `--collect-only`).
5. **Lint:** `.venv\Scripts\ruff.exe check app/projects/service.py tests/test_postgresql.py` → `All checks passed!`, **exit 0**.
6. **Format:** `.venv\Scripts\ruff.exe format --check app/projects/service.py tests/test_postgresql.py` → `2 files already formatted`, **exit 0**.
7. **Whitespace (repo root):** `git diff --check -- backend/app/projects/service.py backend/tests/test_postgresql.py` → empty output, **exit 0** (report file hand-checked for trailing whitespace/EOF; it is untracked, so `git diff --check` covers only the two tracked files, same limitation as F1).
8. **Supplementary (beyond the mandated list, disclosed):** full backend suite `.venv\Scripts\python.exe -m pytest -q` → `163 passed, 10 warnings in 20.53s`, **exit 0**, 0 skipped — confirms no regression in any other suite that exercises `transition_task_status` or the project routes.

## 6. Synthetic databases (created by this task, all preserved — no DROP/reset/cleanup)

Namespace `018_f2`, prefix `conc_task_trans` (11 databases, enumerated read-only via `pg_database`):

- RED phase (pre-fix focused runs, lost update or gate failure observed): `018_f2_conc_task_trans_cf3e39ca` (pre-`populate_existing` fix: both 200, two stale audit rows), `018_f2_conc_task_trans_88cec69d` (both 200, two stale audit rows), `018_f2_conc_task_trans_6301191e` (barrier attribute error run — no transition audit rows, task left `in_progress`), `018_f2_conc_task_trans_42abe32a` (both 200, two stale audit rows), `018_f2_conc_task_trans_3df7703f` (no `FOR UPDATE` yet: gate count 0).
- GREEN phase (post-fix): `018_f2_conc_task_trans_a0f5f685` (cancelled won: exactly one audit row `in_progress → cancelled`, final status `cancelled`), `018_f2_conc_task_trans_950ee952` (module regression run), `018_f2_conc_task_trans_30694071` (stability re-run), `018_f2_conc_task_trans_2278aa64` (stability re-run), `018_f2_conc_task_trans_1ca734b7` (cancelled won: one audit row `in_progress → cancelled`, final `cancelled`), `018_f2_conc_task_trans_1a67bab8` (module-suite run, done won: one audit row `in_progress → done`, final `done`).

Read-only re-query of three GREEN databases (`_diag` helper, `C:\Users\ANHVU\AppData\Local\Temp\opencode\chpmis018_f2_diag.py`, OS temp only) confirmed: exactly one `task:transition` audit row per run, `before_values.status = in_progress`, `after_values.status` matching the winner, final `tasks.status` matching the winner, and one `task:seed` audit row per run.

## 7. Scope compliance

- Modified **only** `backend/app/projects/service.py` and `backend/tests/test_postgresql.py` (plus this append-only report). `git diff --stat` for the two files: 341 insertions / 1 deletion total; `git status` confirms no other product/test file touched by this Worker (pre-existing dirty files such as `backend/app/auth/bootstrap_admins.py` and `backend/tests/test_admin_bootstrap.py` are preserved from other tasks and were not opened for editing).
- No schema, migration, dependency, global authorization, or transition-graph change. No new dependency imported beyond `sqlalchemy.select` (already-provided SQLAlchemy). 400/403/404 response semantics, roles, project authorization, and non-disclosure (404 for inaccessible records) preserved.
- No stage, commit, push, deploy, container start/stop, role-permission change, or other-artifact cleanup performed.

## 8. Limits and open items

- Reproduction/verification uses the in-process `TestClient` + 2-thread pool (same harness shape as the existing preserved concurrency tests), not two separate OS processes.
- The GREEN regression proves serialization on the exercised live path: the barrier forces both requests to read the shared prior `in_progress` state, both complete their row-lock SELECT, and the asserted DB-level outcomes (single audit row, final status, HTTP codes) verify the actual winner regardless of which target won. Interleavings where the two requests never overlap at the database level are indistinguishable from the serialized result by design (both produce the same approved contract), so this test cannot distinguish "fix" from "lucky serial execution" in a non-overlapping run; the overlap is enforced by the bounded barrier for the plain-SELECT stage.
- `populate_existing=True` is essential to the fix (ORM identity-map staleness); removing it re-opens the lost update even with the row lock (observed during this task).
- The pre-existing `statement_timeout=3000` on the engine bounds the row-lock wait for the serialized (losing) request; under normal operation the wait is milliseconds.
- Independent OpenCode Tester and separate OpenCode Reviewer runs are still required for closure; neither the permission-denied F1-T1 evidence nor this Worker report substitutes for them. F1-T1 remains BLOCKED / independently NOT_VERIFIED unless its separate decision is changed.
- No commit was made; all changes remain in the working tree.

## 9. CHPMIS-018-F2-R2 clarification — strengthened gate, corrected count, limitations (appended, historical §1–8 preserved)

This section is appended by the R2 Worker (task pack `.team/tasks/CHPMIS-018-F2-R2-regression-worker.md`, same Feature coding template, ID `cmp1fv5ac0001js04jbj3pxoa`, adapted as assigned). It addresses independent review R1 (`CHANGES_REQUESTED`, 2 P2 / 2 P3). It corrects, does not overwrite: every historical result above remains as originally recorded.

### 9.1 What changed in `backend/tests/test_postgresql.py` (only file modified in R2)

R1 P2-1: the original barrier waited in `before_cursor_execute` on the initial non-locking task SELECT, which proves only that both threads arrived *before execution* of the initial read — a serialized execution could still satisfy the test. The gate now forces the relevant concurrent-read interleaving directly:

- The bounded two-party `threading.Barrier(2, timeout=10.0)` now waits in `before_cursor_execute` on the **row-lock** `SELECT ... FROM tasks ... FOR UPDATE` for the target task. `transition_task_status` issues that statement only after the initial plain task SELECT has returned in the same request thread, so a request reaches the barrier only after its initial read has completed; holding both requests there guarantees **both initial reads finished before either locking SELECT executed**, and neither request holds the row lock while waiting for the other (the wait is before the locking statement executes, not a wait for a second lock acquisition). After the barrier releases, PostgreSQL serializes the row lock itself; the second lock SELECT may block in the database until the first request commits (bounded by the engine `statement_timeout=3000`), and the test only observes completions afterwards. Synchronization is event-based (second party's arrival releases the barrier); the 10 s value only bounds a broken run, so this is not a timer-only race.
- Hook placement: listeners are attached at the `sqlalchemy.engine.Engine` class level (each `TestClient` context builds its own app engine inside the lifespan, after attachment), as before. Per-statement condition: `FROM tasks` + `FOR UPDATE` + target task id in the parameters. This matches only the transition row-lock SELECT: the winner's post-commit `db.refresh(task)` is a plain SELECT, and the app's other `FOR UPDATE` queries target other tables (`system_admin_requests`, `users` in `app/auth/routes.py`). `barrier_passed` is keyed by DBAPI connection `id()`, so it also proves the two requests ran on two distinct pooled connections.
- Listeners are removed in `finally` (both `before_cursor_execute` and `after_cursor_execute`) exactly as before. The removed plain-SELECT barrier bookkeeping is gone; the lock-SELECT completion counter is incremented under a short-lived `threading.Lock` (the two request threads can reach `after_cursor_execute` concurrently), and `barrier_passed` reads happen only after both request threads have joined.
- Preserved unchanged: all HTTP outcome assertions (one 200 / one 400 with the existing invalid-transition or terminal-cancelled detail), winner response status, exactly one `task:transition` audit row with `before.status = in_progress` and `after.status = winner target`, final `tasks.status = winner target`, both preserved admin-approval concurrency tests, and the `lock_selects_completed == 2` observation.
- How the regression exposes stale ORM identity state: with both initial reads forced before either lock read, both requests hold `in_progress` in their ORM identity maps when the locked re-read runs. If the locked re-read does not refresh the already-loaded instance (missing `populate_existing=True`), the loser evaluates against stale `in_progress` and both requests return 200 — the `one 200 / one 400` assertion fails with the "Lost update" message. With no row lock at all, the barrier is never reached (`barrier_passed` stays empty, so the first assertion fails) and the lost update also fails the outcome assertion. Either regression of the fix therefore turns this test red.

### 9.2 What the gate proves and does not prove

- Proves (within the executed run): both concurrent requests read the shared committed `in_progress` state before either executed the row-lock SELECT, and the observed HTTP outcomes, audit row, and final status match the owner-approved serialized contract under that forced interleaving.
- Does not prove: that ordinary, uncontrolled production requests always overlap (they usually will not), or that any other interleaving is excluded or unsafe. The barrier deliberately selects one interleaving for the regression; it is a controlled reproduction, not a statement about production scheduling. A run in which the two requests never overlap at the database level is indistinguishable from the serialized contract by these assertions, and is not what this run tests.
- Does not prove the fix in isolation from the live run: this R2 Worker did not execute live pytest (see §9.5); the claims above are about what the gate would establish when the Coordinator's authorized live verification runs it.

### 9.3 Corrected service-file diff count (R1 P3-1)

Section 3 of this report stated `backend/app/projects/service.py` — 23 insertions, 1 deletion. Corrected, per R1's observation and re-confirmed in R2 by `git diff --numstat -- backend/app/projects/service.py backend/tests/test_postgresql.py`: the service file is **22 insertions / 1 deletion** (23 changed lines). The service file was not modified by R2; only this count statement is corrected.

### 9.4 R1 test finding vs. the factual Tester-error count

- R1 P2-1 is a **test-finding about the regression design** (the plain-SELECT barrier overstates what it proves; addressed in §9.1).
- Separately, R1's narrative repeatedly stated that all six independent Tester commands were denied. The Tester record (`.team/tasks/CHPMIS-018-F2-opencode-tester.md`) establishes that only **command 1** was denied before execution; **commands 2–6 were not attempted** under the stop rule. All six checks remain NOT_VERIFIED. This distinction is recorded so the test finding is not conflated with the (inaccurate) denial count.

### 9.5 Static verification evidence (R2 Worker; live pytest NOT_VERIFIED by this Worker)

This Worker was deliberately not supplied PostgreSQL credentials and made no database, container, or credential access. Exact commands and results:

From `backend/`:

1. `.venv\Scripts\ruff.exe check app/projects/service.py tests/test_postgresql.py` → `All checks passed!`, **exit 0**.
2. `.venv\Scripts\ruff.exe format --check app/projects/service.py tests/test_postgresql.py` → `2 files already formatted`, **exit 0**.

From repository root:

3. `git diff --check -- backend/app/projects/service.py backend/tests/test_postgresql.py .team/tasks/CHPMIS-018-F2-worker-report.md` → empty output, **exit 0**.

Live pytest (focused regression, module regression, related suites) is **NOT_VERIFIED by this R2 Worker** and is to be run separately by the Coordinator using the already-authorized process context, followed by a separate OpenCode review. No pass is claimed here.

### 9.6 Scope deviation record (pre-existing, preserved)

The prior F2 Worker's diagnostic helper `C:\Users\ANHVU\AppData\Local\Temp\opencode\chpmis018_f2_diag.py` (OS temp only) is recorded as the already-disclosed scope deviation (R1 P2-2): a write outside the strict two-file allowlist. R2 did not create, edit, or delete that helper. R2 modified only `backend/tests/test_postgresql.py` and appended this section; no other file, service, container, credential, permission, stage, or commit was touched.

### 9.7 Limitations (R2)

- Static checks only; the strengthened gate has not yet been executed live by this Worker, so its runtime behavior (barrier release, no deadlock, `lock_selects_completed == 2` under the fix, and red behavior under a stale-identity-state or no-lock regression) is inferred from the code path and awaits the Coordinator's authorized live run plus independent OpenCode Tester/Reviewer.
- The barrier is a test-only construct attached to the shared `Engine` class for the duration of the two requests; it must not be interpreted as production synchronization.
- The forced interleaving covers the concurrent-read case only (see §9.2); other races and non-overlapping runs remain outside this regression's claims.
- Task closure is not claimed: independent live verification and separate OpenCode review are still required; F1-T1 remains BLOCKED / independently NOT_VERIFIED.
