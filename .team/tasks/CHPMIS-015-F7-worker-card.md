# CHPMIS-015-F7 — Hermes Worker Card Instructions

## Identity and authority

- **Task ID:** CHPMIS-015-F7
- **Role:** Hermes Backend Worker (implementation)
- **Owner approval:** Recorded 2026-11-02 in `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md` and `OPEN_QUESTIONS.md`.
- **Prompt template:** Real prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved through installed `.agents/skills/prompt-lookup`; modernized prompt is in the approved task pack.
- **Requirement trace:** CHPMIS-015-F6 distinct-request/same-target PostgreSQL defect; mission §6.

## Objective

Use a target-`User` row lock inside the existing approval transaction so two distinct pending grants to the same target serialize. Preserve the exact current conflict behavior: one request returns 200 and one returns 409, with exactly one active canonical `system_admin` role and matching request/session/audit state.

## Allowed files

Modify only:
- `backend/app/auth/routes.py`
- `backend/tests/test_postgresql.py`

No migration/schema/model/constraint/data cleanup, broader permission change, bootstrap change, identity-provider change, or unrelated code/docs edits. Do not stage or commit. Preserve every pre-existing modification and database.

## Required root-cause / TDD order

1. Read `AGENTS.md`, `.team/CHARTER.md`, this card, the approved F7 pack, and `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`. **Do not open the F6 Worker report**, which contains historical test-command material unnecessary for this retry. Coordinator already captured pre-edit `git status`; do not run any git cleanup or restoration command.
2. Owner has provided the approved synthetic loopback PostgreSQL context to this fresh Worker process. Do not locate, inspect, print, or probe that context or any environment value. Immediately reproduce the existing F6 distinct-request same-target test using the exact focused command in the approved pack. It must fail with two 200 responses / duplicate-grant behavior. Record output and exit code without including any URL/credential.
3. If the focused PostgreSQL test is skipped, denied, unavailable, or does not produce the expected live RED, stop before edits and report `BLOCKED / NOT_VERIFIED`. Do not search files for environment names, check ports/services, start/install services, alter host settings, or improvise another database source. Preserve all generated synthetic databases.
4. After a valid live RED, make the smallest route/test-only correction: lock the existing target `User` row with `SELECT ... FOR UPDATE` in the same transaction after request validation/locking and before the existing-role check. Extend/update the regression only as needed to assert exactly one 200 and one 409, one active canonical role, one approved request and one pending request, and target-session revocation. Preserve same-request locking and all existing authority checks.
5. Run only the exact verification commands in `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`. PostgreSQL checks must execute with zero skips for the required live evidence. A skip is `NOT_VERIFIED`, never PASS. Record exact command, working directory, output, exit code, and all skips.
6. Report changed files, live RED/GREEN, final concurrency results, database names (names only; no URL/credential), exact verification, and limits. Request independent review only if all scoped acceptance and live PostgreSQL evidence complete; otherwise block and report the real obstacle. Never self-approve.

## Prohibited actions

- Never read, print, log, or probe environment values or credentials.
- Never print database URLs, connection strings, passwords, tokens, or synthetic secrets.
- Never drop, reset, truncate, or clean databases. Preserve every existing/generated synthetic database.
- Never modify files outside the two-file allowlist; never stage, commit, push, merge, deploy, or access production.
- If the fix appears to need a schema constraint, migration, or broader approval workflow change, stop and request new Human Gate scope.

## Coordinator run outcome (2026-11-02)

- Exact card `t_b936b6d6` was claimed and launched as run 119 in the existing repository workspace; default Hermes profile, no model/provider override surfaced.
- Before edits, the Worker attempted `.venv/Scripts/python -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target` from `backend/`. The tool log shows 6.5 seconds elapsed, but no command output or process exit was captured. Treat this reproduction as `NOT_VERIFIED`; no code edits were permitted or observed.
- The Worker searched for the `TEST_DATABASE_URL` symbol in repository files and read the previous F6 report; it did not print or probe an environment value. It then attempted `powershell -Command "Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue | Select-Object -Property LocalAddress,LocalPort,State"`. Auto-review blocked this as a dangerous script before execution. No host-service status was obtained.
- Coordinator interrupted exec session 99270 (exit 1), reclaimed card `t_b936b6d6`, and blocked it as `needs_input`. No route or test edits were observed. Coordinator `git status --short --branch` from repository root exited 0 with warning `could not open directory 'backend/.pytest-temp/': Permission denied`; branch remains `audit-remediation/verify-audit-findings`, and the F7 allowlist files show only the pre-existing dirty baseline.
- Result: F7 is `BLOCKED / NOT_VERIFIED` before implementation because no live RED evidence exists. Do not retry or use host/credential diagnostics until the approved synthetic test context is made available.

## Owner-provided runtime context and retry authorization (2026-11-02)

- Owner replied “Cung cấp context PostgreSQL tổng hợp cho Worker.” A fresh Hermes process may use the approved synthetic loopback test context. No connection value was shared in chat or added to this task pack.
- A new exact-card attempt is authorized. It must run the focused RED command first and stop before edits if it skips or lacks a captured failure. No environment search or host-service diagnostic is authorized.

## Second exact-card attempt outcome (2026-11-02)

- Created `t_65dab2bf` (`CHPMIS-015-F7 live RED and target-user lock`), claimed only that ID, and launched it directly with `hermes -p default --cli chat -q "work kanban task t_65dab2bf"`; run 121, session `20261102_124043_228fca`, default profile, existing repository workspace, no model/provider override surfaced. Gateway was stopped, so this exact-card manual launch was used; no queue-wide dispatch ran.
- Before edits, from `backend/`, the Worker ran `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target` → `1 skipped, 5 deselected, 1 warning in 4.46s`, exit 0. It reported the approved synthetic loopback PostgreSQL context was not active in that Worker process. This is not live RED evidence.
- Worker stopped before edits and blocked the exact card as `needs_input`. It reported no files or databases were altered. Coordinator `git status --short --branch` exited 0 with the existing warning `could not open directory 'backend/.pytest-temp/': Permission denied`; it shows the pre-existing dirty workspace and no new file paths. Branch remains `audit-remediation/verify-audit-findings`.
- Result: `BLOCKED / NOT_VERIFIED`. The approved context must be made available inside the Hermes Worker process before another RED attempt. No environment value or host diagnostic was read or run in this retry.

## Third exact-card retry authorization (2026-11-02)

- Owner requested another attempt after run 121. Use a fresh exact-ID card and run the approved focused RED command immediately. Do not assume any PostgreSQL context is active. If the command skips or does not capture the expected duplicate-grant RED, stop before edits. The exact two-file scope and no-environment/no-host-diagnostic restrictions remain unchanged.

## Third exact-card attempt outcome (2026-11-02)

- Created `t_b7bf0f51` (`CHPMIS-015-F7 retry focused PostgreSQL RED`), claimed only that ID, and manually launched `hermes -p default --cli chat -q "work kanban task t_b7bf0f51"`; run 122, session `20261102_124524_618c4a`, default profile, existing repository workspace, no model/provider override surfaced. Gateway was stopped; no queue-wide dispatch ran.
- Exact focused command from `backend/`: `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target` → `1 skipped, 5 deselected, 1 warning in 1.57s`, exit 0. Worker said context was not active and blocked before edits; no live RED, product edits, or database changes.
- Worker log shows an additional `git status --short` after the skip. This was outside the immediate-stop sequence. Coordinator `git status --short --branch` exited 0 with the existing warning that `backend/.pytest-temp/` could not be opened; no new paths were observed and the pre-existing dirty paths remain present. Branch remains `audit-remediation/verify-audit-findings`.
- Result: `BLOCKED / NOT_VERIFIED`. Further implementation requires the approved PostgreSQL context to be active in the Worker process. No environment values or host diagnostics were read/run.

## Worker completion contract

Post progress via the card. Finish with exactly one of:
- `kanban_request_review(summary=...)` — only after all scoped checks and live PostgreSQL evidence are complete.
- `kanban_block(reason=...)` — if live PostgreSQL is unavailable/skipped, root cause is not reproduced, a scope/policy choice is needed, or required evidence is missing.

Do not mark the task complete merely because non-PostgreSQL checks pass.
