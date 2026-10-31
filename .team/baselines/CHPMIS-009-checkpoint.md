# CHPMIS-009 — Prepared local checkpoint

## State and authority
This checkpoint is prepared, not staged or committed. HEAD remains `2189d2729139bf66f66f9bd7b8f5c5342cebe5f7`; the candidate tree contains pre-existing tracked edits and untracked backend/frontend/Compose/CI/task files. The owner authorized baseline reconciliation and checkpoint preparation only in CHPMIS-009. No remote exists; no push, deployment or production/provider access is part of this task.

## Candidate inventory
Run `node scripts/audit-baseline.mjs`; Coordinator saves stdout to `CHPMIS-009-candidates.json`. It lists candidate paths, tracked/untracked classification, byte counts and SHA-256. Ignored dependencies, generated outputs and runtime `.env` are not candidate content. Existing `backend/nul` is preserved and ignored. The JSON manifest excludes its own path to avoid self hashing; include that JSON explicitly when preparing a future checkpoint.

The scan checks candidate paths and common high-confidence private-key/token/JWT patterns without printing values. It is heuristic; it cannot establish that every value is synthetic or every secret format is absent. Prior independent AC-15 review remains the content-review evidence. No generated file or discovered value should be added merely because a scan returns no matches.

Product/config initial fingerprint (64 files, excluding the ignored residue): `f535b91c11c5568d0f18f1747a60f926c93b082b8ef7267a4c840ba8a73206a4`.
Initial index fingerprint: `6f690d47fbe52cb757527085e1cd5f7138db82935873b6fd3f15ed1fa68d6562` (no staged modifications). Both must remain unchanged during CHPMIS-009.

## Checks and future checkpoint procedure
1. Read TASKS.md, ACCEPTANCE.md and the manifest; verify candidate paths deliberately include all intended source/config/lockfiles, docs, CI and task evidence.
2. Run `node scripts/audit-baseline.mjs --check .team/baselines/CHPMIS-009-candidates.json`. Any changed/deleted/added candidate or index change invalidates the snapshot. Regenerate and review it after further edits; do not use a stale manifest.
3. Run `git diff --check`, `git add --dry-run --all`, `git status --short`, and `git diff --cached --stat`. Dry-run does not stage files. The current dirty baseline is expected.
4. Actual staging/local commit is a separate subsequent action. At that time, review the exact file list and staged diff (including new files), create the local checkpoint, verify HEAD contains backend/frontend/Compose/CI, then create and inspect a worktree before relying on it. No remote/push is implied.

## Handoff to CHPMIS-010
Recheck Docker/PostgreSQL availability. Before running the existing PostgreSQL integration check, address CHPMIS-009-F1 in a scoped Worker task: backend/tests/test_postgresql.py upgrades to current head but asserts revision 0001 and one technical table. Expected behavior must reflect the existing approved schema through migration 0004. A skipped test or offline SQL generation is not live database evidence.

## Independent gates
CHPMIS-009 independent gates are satisfied: Hermes card t_15f91a2f/run #29 APPROVED with zero P1/P2/P3 findings; final OpenCode retry `2026-10-30T23-34-53-verifier-chpmis-009-t1-verifier-retry-after-confi-767b`, session `ses_e70d56e7cffedMX2CXm1D7mcY8`, completed exactly the five assigned commands with exit 0 and ROLE_RESULT done. Earlier quota failures and the owner's intervening hold remain recorded in T1/ledger history. Coordinator refreshes the manifest after closure evidence/status edits and rechecks it; source/config and index fingerprints must still match the initial values above. Any future candidate change invalidates this snapshot and requires refresh/review. Completion means checkpoint preparation; source is still uncommitted.
