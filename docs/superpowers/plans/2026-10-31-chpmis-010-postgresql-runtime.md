# CHPMIS-010 PostgreSQL Runtime Implementation Plan

> Execute through the established sequential Hermes Worker -> OpenCode Tester -> separate Hermes Reviewer route. Coordinator owns documentation only.

**Goal:** repair the obsolete live PostgreSQL test contract and verify the existing local stack when prerequisites exist.
**Architecture:** test-only assertion/name correction against approved migrations; use real PostgreSQL and existing Compose for runtime evidence, retain explicit skips and runtime blockers.
**Tech Stack:** existing Python/Pytest/Alembic/SQLAlchemy, PostgreSQL 17 Compose configuration; existing dependencies only.
**Spec:** `.team/tasks/CHPMIS-010-postgresql-runtime.md`.

## Global constraints
Worker changes only backend/tests/test_postgresql.py; preserve all other baseline files. No migration/app/config/CI/dependency edits, install/download, destructive database actions, commit/push, provider connection or policy changes. Dirty source cannot be assumed present in a worktree. CHPMIS-009 snapshot remains historical.

## Review focus
Hardcoded obsolete revision/table assertions; exact order-independent current schema checks; retained disposable-DB skip/readiness/disposal behavior; no false PostgreSQL evidence from offline SQL/skips; no sensitive or destructive runtime actions.

## Steps
- [x] Inspect existing test/migrations and confirm current expected revision plus ten-table set; preflight Docker/PostgreSQL tools/listener without printing environment secrets.
- [x] Search/retrieve real Worker prompt via prompt-lookup; bound the test-only fix and runtime runbook.
- [x] Hermes Worker repairs only the existing test and reports focused/full pytest, Ruff and offline SQL output with exact exits. Focused test skipped; no live RED/GREEN claimed.
- [x] OpenCode independently runs full backend pytest (62 passed/1 skipped) and Git whitespace check, both exit 0; role result review because live runtime remains unverified.
- [x] Separate Hermes evidence Reviewer t_a11e6713/run 32 APPROVED, zero P1/P2/P3; no live rerun. Initial runtime Reviewer t_8048cf3f blocked/stopped after safety deviation; results not accepted.
- [x] Execute isolated synthetic runtime runbook and live PostgreSQL verification, then independent review of captured evidence; focused 1 passed/full 63 passed, head/ten tables and health/bind checks confirmed.
- [x] Owner authorized Docker per-user installation; official installer hash/signature verified, install exit 0, CLI/Compose and config validation succeeded. Owner handled first-run agreement and confirmed Engine ready; no automatic license acceptance or reboot.
- [x] Record trace/skills and COMPLETE status, AC-01/03 PASS; 12 PASS/3 NOT_VERIFIED overall. Stop task containers, retain volume, preserve HEAD/index and historical checkpoint.

Runtime executed: focused 1 passed/full 63 passed, both exit 0, initially empty dedicated PostgreSQL migrated to current head/ten tables; Compose/health/loopback checks passed. First Reviewer t_8048cf3f was blocked/stopped; clean evidence-only Reviewer t_a11e6713 APPROVED.


Owner-authorized Coordinator per-user Docker installation is the explicit exception to the initial no-install constraint; role agents did not install. Full results, safety deviation and review attribution are preserved in runtime-evidence.md.
