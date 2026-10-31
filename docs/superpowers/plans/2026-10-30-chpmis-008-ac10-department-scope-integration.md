# CHPMIS-008 AC-10 Department Scope Integration Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add API-level regression evidence that a user whose department matches a project's lead department still has no project/task access without explicit project membership.

**Architecture:** Extend the existing SQLite-backed integration tests in `backend/tests/test_projects.py`, using its current setup and session helpers. Keep implementation and policy unchanged; use one synthetic member and one synthetic project with matching department identifiers and no membership row for that member.

**Tech Stack:** Python 3.13, FastAPI `TestClient`, SQLAlchemy, pytest, SQLite `StaticPool` test database.

**Spec:** `docs/superpowers/specs/2026-10-30-chpmis-008-ac10-department-scope-integration-design.md`

## Global Constraints

- Approved policy: explicit project membership is required; department membership alone grants no project access.
- Do not change auth policy, routes, schemas, migrations, business workflow, dependencies, or runtime code.
- Use synthetic fixture values only; preserve the existing dirty/untracked repository baseline.
- Tester and Reviewer are read-only; dispatch sequentially against the existing repository directory.

## Review Focus

1. The test really establishes `user.department == project.lead_department_id` and no `ProjectMember` row for the caller.
2. Project and task lists do not reveal the matching-department project or task.
3. Guessed project/task identifiers return non-disclosing 404s for reads.
4. A valid-CSRF task transition and project archive attempt are denied before state change.
5. Denied writes add no transition/archive audit event; dashboard and audit reads remain scoped.

---

### Task 1: Add one department-matched, nonmember integration scenario

**Files:**
- Modify: `backend/tests/test_projects.py`

**Interfaces:**
- Reuse: `setup_test_env()` and `create_user_and_session()` in `backend/tests/test_projects.py`.
- Exercise: existing `/api/v1/projects`, project member, task list/read/status, dashboard, archive, and audit-events routes.

- [x] Worker added `test_department_match_without_explicit_project_membership_is_denied_ac10` using a synthetic department ID on the project and user, without inserting a membership for the test user.
- [x] Test asserts project list/dashboard omit the project; project, member, task, and audit reads return 404.
- [x] With a valid CSRF token, task transition and project archive return 404; task remains `open`, project remains `active`, and neither denied action has an audit event.
- [x] Worker ran focused test: `.venv\Scripts\python.exe -m pytest -q tests/test_projects.py::test_department_match_without_explicit_project_membership_is_denied_ac10` from `backend/` — 1 passed, exit 0 (Worker report).
- [x] Worker ran full backend suite: `.venv\Scripts\python.exe -m pytest -q` from `backend/` — 62 passed, 1 skipped, exit 0 (Worker report).
- [x] Worker ran backend lint: `.venv\Scripts\ruff.exe check .` from `backend/` — passed, exit 0 (Worker report).
- [ ] OpenCode Tester independently ran the focused test and full suite — BLOCKED before command execution by `permission.rejected: Permission denied: shell`; independent test outcomes remain `NOT_VERIFIED`.
- [x] Hermes Reviewer completed static review — APPROVED, zero P1/P2/P3 findings; two P4 informational notes.

**Observed verification:** Worker reports focused/full pytest and Ruff pass. The independent OpenCode Tester could not execute pytest because the shell permission was denied, so do not represent those results as independently reproduced. Because this is regression coverage for existing behavior, no temporary policy mutation or artificial red run is permitted.

**Completion:** Worker reports only the allowed test file and exact checks. Hermes Reviewer approved static source/scope review without edits. CHPMIS-008 remains partial until independent OpenCode execution is available; AC-10 remains PARTIAL.
