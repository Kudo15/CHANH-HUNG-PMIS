# CHPMIS-009 Baseline Readiness Implementation Plan

> Execute as Codex Coordinator for documentation/audit tooling, OpenCode read-only Tester, and a separate Hermes Reviewer, following the existing project role routing.

**Goal:** prepare an auditable candidate checkpoint and truthful current-state documents through CHPMIS-008.
**Architecture:** read-only Git/file inventory and heuristic candidate scan; preserve source and index. Reconcile current summaries against recorded independent evidence; preserve historical task snapshots.
**Tech Stack:** existing Node.js and Git; Markdown/JSON documentation.
**Spec:** `.team/tasks/CHPMIS-009-baseline-readiness.md`, including the owner's CHPMIS-009 roadmap scope.

## Global constraints
Only task-pack allowed files may change. No product edits, installs, staging/commit, remote/provider access, deployment, or acceptance promotion. Keep 10 PASS and 5 NOT_VERIFIED criteria.

## Review focus
Candidate secrets/generated/reserved files; snapshot self hashing; stale results presented as current; unchanged product and Git index; premature worktree/runtime claims.

## Steps
- [x] Capture initial Git state, HEAD/index and product/config content fingerprints.
- [x] Add read-only inventory/heuristic scan and exclude the existing backend/nul residue.
- [x] Reconcile current README, PLAN, TASKS, ACCEPTANCE, MISSION, routing and execution rulings; record PostgreSQL-test drift as an explicit follow-up.
- [x] Produce candidate manifest and checkpoint instructions; run task-pack checks.
- [x] Dispatch read-only OpenCode Tester, then independent Hermes Reviewer; capture five successful raw command events and APPROVED review with no P1/P2/P3 findings. OpenCode harness itself FAILED on quota.
- [x] Owner reported readiness; final retry run 2026-10-30T23-34-53-verifier-chpmis-009-t1-verifier-retry-after-confi-767b completed exactly five commands, exit 0, ROLE_RESULT done. Earlier failed attempts remain historical.
- [x] Record final retry/skills trace, close task and refresh/check final manifest. Source/config and index preserved; checkpoint prepared, not committed. No application/runtime acceptance criteria promoted.
