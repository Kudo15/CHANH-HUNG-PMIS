# CHPMIS-015-F6-R1 — Independent Review of Distinct-Request PostgreSQL Repro

- **Task ID:** CHPMIS-015-F6-R1
- **Role:** Hermes Reviewer (read-only)
- **Status:** COMPLETE — APPROVED (0 P1/P2/P3)
- **Scope:** Review only the F6 change in `backend/tests/test_postgresql.py`, `.team/tasks/CHPMIS-015-F6-distinct-request-same-target-pg-repro.md`, and `.team/tasks/CHPMIS-015-F6-worker-report.md`.
- **Requirement trace:** Mission §6 Priority 3 concurrency; task pack `.team/tasks/CHPMIS-015-F6-distinct-request-same-target-pg-repro.md`.
- **Prompt template:** Not applicable; read-only Reviewer task.
- **Evidence:** Hermes Reviewer card `t_5338365e`; independently verified test synchronization, contract assertions, database isolation/preservation, preservation of existing same-request concurrency contract, and live PostgreSQL RED output.

---

## 1. Scope and Boundary Compliance

- Allowed files modified/created by Worker:
  - `backend/tests/test_postgresql.py` (added `test_postgresql_distinct_requests_same_target_concurrency` and event/barrier helpers).
  - `.team/tasks/CHPMIS-015-F6-worker-report.md` (authored report).
- Zero product code, schemas, models, or migrations were modified.
- Strict isolation: All synthetic entities use `syn_dist_*` prefixes. Synthetic databases are uniquely named (`chpmis_013_distinct_target_*`) and preserved without drops or resets.
- Card `t_9a17eb5a` remains BLOCKED for a separately approved fix task.

---

## 2. Technical Evaluation of Concurrency Reproduction

1. **Deterministic Synchronization:**
   - Uses `threading.Barrier(2, timeout=10.0)` hooked via SQLAlchemy `before_cursor_execute` event on `engine`.
   - Traps the `SELECT ... FROM user_roles` query matching `target_user.id` (the `existing_grant` check in `app.auth.routes.approve_system_admin_role_request`).
   - Ensures both approval transactions reach and evaluate the existing-role check concurrently before either thread can insert a new role record or commit.
   - Clean lifecycle: Listener removal in `finally:` via `event.remove(engine, "before_cursor_execute", before_cursor_execute)` and engine disposal.

2. **Safe Contract Assertions:**
   - Status code distribution: `assert sorted(status_codes) == [200, 409]`.
   - Conflict detail validation: Asserts `already` or `conflict` in 409 response detail.
   - Target role count: `assert len(roles) == 1` for active canonical `system_admin`.
   - Target session revocation: `assert tgt_sess.is_revoked is True`.
   - Single approved request: `assert approved_count == 1`.

3. **Preservation of Existing Concurrency Contract:**
   - Existing same-request concurrency test `test_postgresql_concurrent_approval_serialized` remains intact and passes against live PostgreSQL.

4. **Live PostgreSQL Defect Demonstration:**
   - Independently reproduced live PostgreSQL execution:
     - `pytest -q tests/test_postgresql.py -k distinct_requests_same_target` -> FAILED (exit 1) with `AssertionError: Expected one 200 and one 409: [(200, ...), (200, ...)]`, `assert [200, 200] == [200, 409]`.
     - Full PostgreSQL suite: 4 passed, 1 failed (exit 1).
     - Default execution without `TEST_DATABASE_URL`: 5 skipped (exit 0).
     - Scoped Ruff check and format check: exit 0.
   - Defect confirmed: `app/auth/routes.py` locks only `SystemAdminRequest` by request ID (`with_for_update()`), leaving distinct requests for the same target user uncoordinated. Under Read Committed isolation, both threads observe no existing role and insert duplicate `system_admin` roles because `user_roles` lacks a unique constraint on `(user_id, role)`.

5. **RED-before-file-change Sequence Compliance:**
   - Worker executed baseline check before test addition (exit 5, deselected).
   - Worker implemented test and verified live RED failure (exit 1).
   - Worker halted per contract without attempting an unauthorized product fix.

---

## 3. Findings

- **P1 Findings:** 0
- **P2 Findings:** 0
- **P3 Findings:** 0

---

## 4. Verdict

**APPROVED**. The test faithfully and deterministically reproduces the distinct-request same-target concurrency defect on live PostgreSQL while strictly preserving project boundaries, isolation, and existing test contracts. Implementation card `t_9a17eb5a` remains BLOCKED pending Human Gate approval for a dedicated product fix task.
