# Task Pack — CHPMIS-013 PostgreSQL Schema, Migration and CI Contract

## Task ID, role and status

- **Task ID:** CHPMIS-013
- **Trace:** Audit findings A1-01 through A1-04; mission §4 A1; platform acceptance AC-01/03/04; CHPMIS-010 migration contract.
- **Roles:** Hermes Worker (only implementation/test/config writer), OpenCode Tester (read-only), separate Hermes Reviewer (read-only), Codex Coordinator (runtime evidence and records).
- **Status:** COMPLETE — Worker run #63, OpenCode verification, live Coordinator PostgreSQL/Compose evidence, and independent Hermes Reviewer `t_23585fca`/run #64 APPROVED (0 findings). A1-04 remains an explicitly confirmed unsafe downgrade limitation; remote CI and authenticated E2E are outside this task and NOT_VERIFIED.
- **Baseline:** Preserve the current dirty worktree and branch `audit-remediation/verify-audit-findings`; do not reset, stash, clean, commit, push or create a remote.

## Context

Audit A1-01: `backend/tests/test_postgresql.py` still asserts revision `0004_projects_tasks_audit` and ten tables, while the current head is `0005_initial_admin_bootstrap` and adds `admin_bootstrap_receipts`. CHPMIS-010's live `chpmis010` project and named volume are historical evidence and must remain untouched.

Audit A1-02: CI runs `docker compose config --quiet` with `POSTGRES_PASSWORD` and `DATABASE_URL`, but Compose also requires four Keycloak/OIDC interpolation values even though the opt-in service is not started. Supply synthetic placeholders to that validation step only; do not expose or add real credentials.

Audit A1-03: `ruff format --check .` fails on the existing revision `0005_initial_admin_bootstrap.py` and `backend/tests/test_projects.py`.

Audit A1-04: revision 0005 makes `user_roles.granted_by` nullable. Its downgrade attempts to restore NOT NULL, which may fail after bootstrap-created rows with `granted_by = NULL`. Establish behavior with synthetic disposable PostgreSQL data and report the boundary. Do not call rollback safe unless the test proves it.

## Objective

Make PostgreSQL tests assert the real head revision and exact head table contract, verify an empty database upgrade and a populated revision-0004-to-head upgrade on isolated synthetic PostgreSQL databases, make CI's Compose validation resolve using synthetic values, resolve the two formatting failures, and record actual downgrade behavior after bootstrap-like data exists.

## Worker allowlist

The Worker may change only:

- `backend/tests/test_postgresql.py` — update the meaningful revision/table contract and test assertions needed for the migration contract; retain `TEST_DATABASE_URL` gating and do not weaken assertions.
- `backend/alembic/versions/0005_initial_admin_bootstrap.py` — formatting only; preserve migration semantics and historical revision metadata.
- `backend/tests/test_projects.py` — formatting only for the two reported formatter violations.
- `.github/workflows/ci.yml` — add only synthetic interpolation values to the Compose validation step, scoped to that step.
- Append only: `.team/tasks/CHPMIS-013-worker-report.md`.

Do not add/edit migrations, rewrite applied migration history, alter schema semantics, delete/reset/drop databases, touch `.env`, change Compose service behavior, add dependencies, weaken CI checks, or modify any other file. If a safe correction requires a schema change or a different file, stop and report the exact evidence plus a narrowly scoped follow-up proposal; do not infer Human Gate approval.

## Required work and evidence

1. Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this pack, `CHPMIS-010-postgresql-runtime.md`, audit register, acceptance/security/data model, and current `git status` before work. Preserve all CHPMIS-014 and pre-existing modifications.
2. Inspect actual migration head and schema contract. Update `test_postgresql.py` to assert revision `0005_initial_admin_bootstrap` and the exact set of eleven tables, including `admin_bootstrap_receipts`; retain real PostgreSQL inspector/SQL and readiness checks.
3. Add meaningful coverage or a repeatable scoped runbook for both an empty database upgrade and a populated synthetic revision-0004 upgrade. Use only newly created task-specific databases in the isolated CHPMIS-013 PostgreSQL service. Never use, reset, migrate, or stop `chpmis010` resources. Record initial revision/table/row evidence and resulting head schema; do not erase databases on closeout.
4. Reproduce the CI Compose validation environment, then add only synthetic placeholders for `KC_BOOTSTRAP_ADMIN_PASSWORD`, `OIDC_CLIENT_SECRET`, `KC_SYNTHETIC_ADMIN1_PASSWORD`, and `KC_SYNTHETIC_ADMIN2_PASSWORD` to the validation step. Re-run `docker compose config --quiet` with exactly the workflow's environment contract; never start Keycloak for this check or print values.
5. Run Ruff formatting on the two reported files and inspect the diff to ensure formatting caused no semantic migration change.
6. With a synthetic bootstrap-like row having `granted_by = NULL`, attempt downgrade only in a task-created disposable database. Record the exact result. If downgrade fails or is unsafe, preserve the result and leave rollback marked unsafe/unverified; do not edit migration semantics or claim success.
7. Report exact commands, working directories, outputs, exit codes, test counts/skips, PostgreSQL version, initial/final revisions and schemas, changed-file list, TDD/evidence order, and every NOT_VERIFIED or blocked criterion. No commit.

## Verification commands

From `backend/` (all commands must be repository-defined or listed here):

1. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check .`
5. `.venv\Scripts\python.exe -m alembic upgrade head --sql` — offline SQL evidence only; not a substitute for live PostgreSQL.

From repository root:

6. `docker compose config --quiet` with only the exact synthetic values provided by the CI validation step (configuration check only; do not start services).
7. `git diff --check`.

The Worker reports checks but does not self-approve the DoD. OpenCode independently reruns feasible assigned checks read-only and reports any environment limitation. The Coordinator records live PostgreSQL/Compose evidence. A separate Hermes Reviewer inspects the final scoped diff, task requirements, Worker/Test evidence and limitation statements without modifying files.

## Local runtime boundaries

- If Docker is available, use a new Compose project name `chpmis013`, loopback-published ports only, synthetic process-only credentials and a fresh task-specific volume. First inspect only `chpmis013` state and required ports. Preserve `chpmis010` and its volume exactly.
- Create distinct empty and populated-upgrade test databases inside only the CHPMIS-013 PostgreSQL instance. The populated path starts at revision `0004_projects_tasks_audit` with synthetic rows, then upgrades to `head`; capture schema before/after.
- No `.env` reads/writes, no production, no remote, no real agency data, no real IdP, and no real credentials. Never print passwords or connection strings containing passwords.
- Preserve task databases/volume for review. Do not issue `DROP DATABASE`, volume removal, global Docker cleanup, or any operation against another Compose project.
- If the service cannot be safely isolated or a required port conflicts, stop runtime work and report BLOCKED/NOT_VERIFIED; do not repurpose or stop another project.

## Prompt template requirement

- **Library:** installed `.agents/skills/prompt-lookup` via prompts.chat MCP.
- **Template:** “Feature coding template,” Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved 2026-10-31: https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template
- **Modernized Worker prompt:** “Act as the Python/PostgreSQL migration-contract Worker for CHPMIS-013. Follow this task pack and the retrieved Feature coding template. Read the charter, ledger, acceptance contract, CHPMIS-010 evidence and current dirty status first. Work only in the allowlist. Keep schema assertions exact and meaningful; use isolated synthetic databases for empty and populated-0004 upgrades. Fix only the named Ruff formatting violations and CI interpolation values. Do not rewrite an applied migration or alter schema/authorization/workflow semantics. Establish downgrade behavior with synthetic data and report an unsafe result without masking it. Preserve all existing work; run only the listed checks; record exact commands, output, exit codes and limitations; do not commit. Stop for a scoped follow-up if safe progress needs files or policy outside this pack.”

## Definition of Done

- Test contract matches current migration head and exact schema.
- Empty and populated prior-schema upgrade evidence comes from live disposable PostgreSQL; SQLite and offline SQL do not count.
- CI Compose config passes with placeholders scoped to validation only.
- The two listed formatter violations are resolved without semantic migration change.
- Downgrade after bootstrap-like nullable `granted_by` data has an observed, accurately reported outcome; unsafe rollback remains explicitly unsafe.
- Worker report, independent OpenCode Tester evidence, independent Hermes Reviewer verdict, Coordinator runtime evidence, requirement trace and ledger entry are present for the same final working diff.
- No work outside the allowlist, no reset/drop/destruction, no commit/push/deploy, and no unsupported completion claim.

## Hermes card closing contract

ROLE: worker (implementation). Work only in this task's repository workspace. Follow the task pack and keep one task at a time. Post progress with `kanban_comment`. Finish by calling exactly one of `kanban_request_review(summary=...)`, `kanban_block(reason=...)`, or `kanban_complete(result=...)`; include changed files, exact verification evidence, requirement trace and unresolved limits. Do not commit.
