# CHPMIS-009 — Baseline readiness and documentation reconciliation

- Task ID: CHPMIS-009; authorized by owner on 2026-10-31.
- Roles: Codex Coordinator (documentation and audit tooling), independent OpenCode Tester, independent Hermes Reviewer. No product-code Worker is required for this scope.
- Status: COMPLETE — final OpenCode verifier retry executed exactly five assigned commands, all exit 0, and returned ROLE_RESULT done; independent Hermes review APPROVED with zero P1/P2/P3 findings. Checkpoint prepared, not staged/committed.
- Objective: reconcile current state through CHPMIS-008, inventory checkpoint candidates, and prepare a reviewable local checkpoint without staging or committing existing work.
- Trace: mission reproducibility/DoD; AC-04 and AC-15 evidence hygiene. Do not promote runtime acceptance criteria.
- Existing templates: Tester `Test Engineer Agent Role`, prompts.chat `cmmx34zl7000vil04rm2wl8yl`; Reviewer `Senior Code Reviewer (severity-ranked)`, `cmv9n79m30005ku060pzornri`. Previously retrieved via prompt-lookup and adapted in CHPMIS-007/008 task packs. No new prompt search or Worker dispatch is claimed.

## Allowed files
Current-state documentation: README.md, PLAN.md, TASKS.md, ACCEPTANCE.md, OPEN_QUESTIONS.md, docs/MISSION.md, .team/routing.json, .team/ledger.md, .gitignore.
New artifacts: this pack; .team/tasks/CHPMIS-009-T1-test-evidence.md; .team/tasks/CHPMIS-009-R1-independent-review.md; .team/baselines/CHPMIS-009-candidates.json; .team/baselines/CHPMIS-009-checkpoint.md; scripts/audit-baseline.mjs; docs/superpowers/plans/2026-10-31-chpmis-009-baseline-readiness.md.
Product files, dependencies, schema/auth/workflow policy and historical task results are outside the write scope. Preserve all pre-existing changes. Do not stage, commit, push, create a remote, deploy, install dependencies, or connect providers. Keep historical evidence explicitly historical; fix current summaries rather than rewrite old results.

## Definition of Done
1. Current docs reflect CHPMIS-003–008 completion, 10 PASS / 5 NOT_VERIFIED criteria, correct active routing, current migration chain and dated command evidence.
2. Audit inventories tracked and untracked Git candidates, byte hashes, index fingerprint and source/config fingerprint; rejects candidate generated/private/reserved paths and high-confidence secret patterns without printing values. Heuristic scanning is not a guarantee that content is non-sensitive.
3. Existing backend/nul is preserved and ignored. Checkpoint manifest excludes only its own JSON to avoid self hashing. Checkpoint instructions explain that a prepared manifest does not put source into HEAD or make worktrees ready.
4. Run the commands below; independent OpenCode verifies them read-only; Hermes independently reviews documentation, scope, evidence and checkpoint safety.
5. Record findings, exact results/exit codes, roles/skills/run traces and next-task handoff in ledger. Do not claim completion until Tester and Reviewer gates pass.

## Owner steering history and closure
On 2026-10-31, owner chose to repair OpenCode quota/model and keep CHPMIS-009 waiting for a rerun. Existing raw OpenCode execution evidence and Hermes approval are retained, but do not mark the task COMPLETE until the owner reports configuration is ready and a complete verifier rerun is recorded. Preserve configured model inheritance; do not change provider/model or dispatch a fallback Tester. Refresh the manifest before retry if any candidate changes.

Owner subsequently reported `OpenCode đã sửa xong`, authorizing the retry. Preflight and the existing manifest check passed; source/config and index hashes still match the original baseline. Rerun only the five commands in T1, one per call, then provide the complete handoff. Prior failed run remains historical.

Retry run `2026-10-30T23-31-01-verifier-chpmis-009-t1-authorized-complete-verifi-6be9` failed with the same `Free usage limit reached` response, exit 1, no shell execution events, all token counters 0. Preserve the owner's request to wait for a complete OpenCode run; no fallback/model/provider change is authorized. Previous five successful command events and Hermes approval remain evidence, but task completion stays pending.

Closure: owner again reported repair and requested retry. Run `2026-10-30T23-34-53-verifier-chpmis-009-t1-verifier-retry-after-confi-767b`, session `ses_e70d56e7cffedMX2CXm1D7mcY8`, completed status done, exit 0, ROLE_RESULT done. Raw tool events contain exactly the five assigned shell commands, all exit 0, and only read tools otherwise. It confirmed 125 candidates, 64 unchanged product/config files, original index fingerprint, no scan findings, correct routing and 10 PASS/5 NOT_VERIFIED. Existing Hermes review card t_15f91a2f/run 29 remains APPROVED; only evidence/status documentation changed after that review. No source/audit implementation changes, additional Reviewer run, staging, commit or remote action was performed. Coordinator refreshes the final manifest and rechecks it after closure edits.

## Verification commands (repository root)
- `node scripts/audit-baseline.mjs` — JSON inventory to stdout, exit 0 only if checks pass; Coordinator saves stdout as the manifest.
- `node scripts/audit-baseline.mjs --check .team/baselines/CHPMIS-009-candidates.json` — compare current candidate hashes with saved manifest.
- `git diff --check` — whitespace check of tracked modifications.
- `git add --dry-run --all` — checkpoint feasibility; must not stage anything.
- `git status --short` and `git diff --cached --stat` — observe dirty baseline and unchanged empty index.
No application regression suite is required for documentation/audit tooling only. No Docker/PostgreSQL/IdP/CI execution is claimed.

## Known follow-up
- CHPMIS-009-F1 (P2, proposed CHPMIS-010 scope): backend/tests/test_postgresql.py upgrades to head but asserts revision 0001 and only alembic_version; migrations now reach 0004. The test is skipped without TEST_DATABASE_URL. Worker must update this existing verification to inspect the approved current schema before using it as PostgreSQL evidence. Source observation, not a newly executed failure.
