# CHPMIS-012-F1 — Proposed Hermes Tester Fallback

- **Task ID:** CHPMIS-012-F1-T1-HERMES
- **Role:** Independent Tester / Verifier (read-only)
- **Status:** `BLOCKED — PROCESS SCOPE DEVIATION`
- **Purpose:** Resolve the remaining F1 verification gate after the approved OpenCode `role-verifier` could not execute shell commands.
- **Requirement trace:** CHPMIS-012 / mission §5; AC-05; `.team/CHARTER.md`; `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; `.team/tasks/CHPMIS-012-F1-R2-atomic-consumption-cookie-cleanup.md`; `.team/tasks/CHPMIS-012-F1-R3-test-scope-cleanup.md`.

## Owner approval

On 2026-11-02 the owner approved one independent, read-only Hermes Tester run as a substitute harness for the already approved OpenCode verification payload in `.team/tasks/CHPMIS-012-F1-R2-R3-open-code-verifier.md`. This changes only the Tester harness/role assignment for this F1 verification. It does not authorize implementation, new checks, environment inspection, permission changes, provider/model changes, or any production/runtime action.

Reason: OpenCode run `2026-11-02T02-53-03-verifier-chpmis-012-f1-final-read-only-verificati-467b` read the approved evidence, but the `role-verifier` shell tool was denied before execution (`Permission denied: shell`). None of the seven commands ran and all seven remain `NOT_VERIFIED`. The final independent Hermes Reviewer has already approved the F1/R2/R3 scope with zero findings (card `t_f9a9870e`, run 114); live PostgreSQL remains `NOT_VERIFIED` because `TEST_DATABASE_URL` is unset.

## Proposed scope and DoD

After explicit owner approval, a fresh independent Hermes Tester session may inspect only the approved F1 task/evidence files and the scoped F1 diff named in the OpenCode verifier pack. It must distinguish the F1 `/login` and `/callback` cookie glue in `backend/app/auth/routes.py` from unrelated pre-existing route changes. It must not modify files, index, HEAD, or branch.

Run only the seven commands listed below, from the exact working directories. Record each exact command, working directory, output summary, and process exit code. Report a PostgreSQL skip as `NOT_VERIFIED`. If shell/tool access is denied or a command is unavailable, report `NOT_VERIFIED` without changing permissions/settings or retrying through another harness. No extra check is authorized.

Do not inspect, print, or probe `TEST_DATABASE_URL` or any environment value. Do not run Docker, Keycloak, network/provider calls, mutating formatters, or cleanup commands. Preserve all existing workspace changes. Do not commit, push, merge, deploy, or access production.

### Exact verification commands

1. Working directory `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. Working directory `backend/`: `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
3. Working directory `backend/`: `.venv\Scripts\python.exe -m pytest -q`
4. Working directory `backend/`: `.venv\Scripts\ruff.exe check . ../dev`
5. Working directory `backend/`: `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py`
6. Working directory `backend/`: `.venv\Scripts\python.exe -m alembic upgrade head --sql`
7. Working directory repository root: `git diff --check`

## Available evidence before dispatch

- OpenCode run above: all seven checks `NOT_VERIFIED`; shell denied before any command, no process exit codes.
- Independent Hermes Reviewer: final F1/R2/R3 diff `APPROVED`, 0 P1/P2/P3; see `.team/tasks/CHPMIS-012-F1-R2-R3-independent-review.md`.
- Worker run 110 and R2/R3 reports contain focused/full pytest and Ruff evidence; PostgreSQL was skipped/unset and therefore remains `NOT_VERIFIED`. See `.team/tasks/CHPMIS-012-F1-worker-report.md` and `.team/tasks/CHPMIS-012-F1-R2-worker-report.md`.
- Full prior output and restrictions are in `.team/tasks/CHPMIS-012-F1-R2-R3-open-code-verifier.md`.

## Dispatch controls

The harness substitution approval was recorded above. Hermes gateway preflight reported that the gateway was stopped. The initial helper used a broad queue dispatch and selected an unrelated F3 card; that run was reclaimed immediately. The exact F1 card was then manually claimed and launched. This launch is now blocked after a scope deviation described below. Do not retry this card or change verifier permissions/settings without a new owner direction.

## Coordinator execution outcome

- Owner approval: “Duyệt Hermes Tester chỉ đọc” (2026-11-02), for one independent read-only run.
- Preflight: sandbox invocation of `hermes --version; hermes kanban boards show; hermes gateway status` exited 1 because the Hermes install lock was not writable. The reviewed elevated retry exited 0: Hermes v0.21.6+774.g835c3dd; board `default`; gateway stopped. No persistent gateway was started.
- Dispatch deviation: helper `hermes-role-task.mjs` created card `t_b6265dce` but its broad `hermes kanban dispatch --max 1` spawned unrelated CHPMIS-017-F3 card `t_e4f5224f`, run 115, PID 142268. Coordinator immediately reclaimed it; event metadata confirms `terminated=true`. No F3 code changes were observed. Do not dispatch that unrelated card again as part of F1.
- F1 exact-card run: card `t_b6265dce`, run 116, default profile, existing repository workspace, no model/provider override. The verifier executed an extra `git status` command (working directory repository root; exact output and process exit were not captured) before running any of the seven checks. Coordinator interrupted the run, reclaimed the card, then blocked it as `needs_input`. Hermes log command returned `(no log for t_b6265dce — task may not have spawned yet)` with exit 1. No verifier result or session ID was produced.
- Exact command results (none were observed to run; no process exit codes):

| # | Command | Working directory | Result |
|---|---|---|---|
| 1 | `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py` | `backend/` | `NOT_VERIFIED` — stopped before command |
| 2 | `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py` | `backend/` | `NOT_VERIFIED` — stopped before command |
| 3 | `.venv\Scripts\python.exe -m pytest -q` | `backend/` | `NOT_VERIFIED` — stopped before command |
| 4 | `.venv\Scripts\ruff.exe check . ../dev` | `backend/` | `NOT_VERIFIED` — stopped before command |
| 5 | `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py app/auth/models.py app/config.py tests/test_auth_oidc.py tests/test_postgresql.py` | `backend/` | `NOT_VERIFIED` — stopped before command |
| 6 | `.venv\Scripts\python.exe -m alembic upgrade head --sql` | `backend/` | `NOT_VERIFIED` — stopped before command |
| 7 | `git diff --check` | repository root | `NOT_VERIFIED` — stopped before command |

- No `TEST_DATABASE_URL` or other environment value was inspected by Coordinator.
- Repository preservation check by Coordinator: `git status --short --branch` at repository root, exit 0 (warning: could not open `backend/.pytest-temp/`). The listed source modifications match the pre-dispatch dirty workspace; no new product-code changes were observed. The branch remains `audit-remediation/verify-audit-findings`.
- Result: F1 verification remains blocked. The single approved fallback attempt was stopped for the out-of-pack command; do not dispatch a further Tester without fresh owner direction.
