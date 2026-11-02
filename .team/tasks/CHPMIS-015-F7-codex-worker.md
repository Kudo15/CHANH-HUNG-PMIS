# CHPMIS-015-F7 — Codex Worker Assignment

## Role, authority, and trace

- **Task:** CHPMIS-015-F7; backend authorization Worker.
- **Prompt template:** Real prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`; project-modernized prompt in `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`.
- **Requirement trace:** CHPMIS-015-F6 distinct pending requests to the same target; mission §6; `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`.
- **Owner direction:** Owner approved a separate synthetic PostgreSQL 17 runtime on `127.0.0.1:55432`, with unique Compose project/volume and a short-lived launcher that injects `TEST_DATABASE_URL` into this Codex Worker process. Do not inspect, print, copy to output, or search for any environment value or secret.

## Objective and allowed files

Serialize distinct pending System Admin grants for the same target `User` by locking that existing User row with `SELECT ... FOR UPDATE` inside the same approval transaction, before the existing-role check. Preserve the existing conflict behavior: one 200 and one 409; exactly one active canonical `system_admin`; one approved request and one still pending; target-session revocation.

Modify only:

- `backend/app/auth/routes.py`
- `backend/tests/test_postgresql.py`

No migration/schema/model/constraint, cleanup, permission or broader workflow changes. Do not stage, commit, push, merge, or deploy. Preserve all existing files and databases.

## Required first action: live RED

1. With the approved process-local synthetic `TEST_DATABASE_URL` injected by the launcher, without inspecting configuration or running any preparatory shell command, run this exact focused command from `backend/` as the first command:

   `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`

2. Capture exact output and exit code without any URL or secret. Valid RED requires the existing duplicate-grant behavior (two 200 responses / duplicate canonical role).
3. If the test skips, is unavailable, or does not show the expected live RED, stop immediately. Run no further command, including `git status`; read no more files; make no edits. Report `BLOCKED / NOT_VERIFIED` with the exact test result.

## After a valid live RED only

- Read `AGENTS.md`, `.team/CHARTER.md`, this task, `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`, and `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`. Do not open the F6 Worker report.
- Follow TDD. Make the smallest implementation and regression-test changes only in the two allowed files. Preserve all existing authorization checks, request-row locking, responses, audit fields, sessions, and bootstrap behavior. Isolate F6's test database namespace. Never drop, reset, truncate, or clean databases.
- Run only the exact verification commands listed in `.team/tasks/CHPMIS-015-F7-target-row-lock-fix-proposal.md`, recording working directory, output, exit code, and skips. A PostgreSQL skip is `NOT_VERIFIED`, never PASS.
- Request independent review only after all live PostgreSQL acceptance evidence is complete. Do not self-approve.

Finish with a concise report of changes and evidence, or the exact blocker.

## Codex Worker attempt result (2026-11-02)

- Worker: `/root/chpmis015_f7_worker`; delegated in a fresh Codex subagent context for CHPMIS-015-F7.
- Its first and only shell command, from `backend/`, was `.venv/Scripts/python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`.
- Result: exit 0; `1 skipped, 5 deselected, 2 warnings in 1.41s`. No live duplicate-grant RED was produced. The Worker stopped without further commands, file reads, or edits and reported `BLOCKED / NOT_VERIFIED`.
- Coordinator post-run `git status --short --branch` exited 0 with the known warning that `backend/.pytest-temp/` could not be opened. No new product paths appeared; the pre-existing dirty F7 files remain modified. F7 remains blocked pending actual test-context availability within the Codex Worker process.

## Isolated runtime retry outcome (2026-11-02)

- Launched a fresh Codex CLI Worker with the approved process-local `TEST_DATABASE_URL`. Its exact first command exited 1 during pytest plugin import: Python `OSError: [WinError 10106]` while importing `_overlapped` through `anyio`. The test did not execute; the Worker stopped without other commands, reads, or edits.
- Coordinator then ran the exact focused test from `backend/` using the same synthetic isolated database context. Result: exit 0; `1 passed, 5 deselected, 2 warnings in 17.61s`. No expected live duplicate-grant RED was observed. Under the current task stop gate, do not edit code or run further attempts; F7 is `BLOCKED / NOT_VERIFIED`.

## Bounded read-only diagnosis follow-up

- Owner authorized `.team/tasks/CHPMIS-015-F7-reproduction-diagnosis.md`, read-only, maximum five focused test invocations. One additional Coordinator invocation exited 1 with `1 failed, 5 deselected, 2 warnings in 6.05s`; the assertion output recorded two HTTP 200 approvals for distinct requests to the same target. No code was edited.
- Diagnosis: the existing `before_cursor_execute` barrier does not guarantee both target-role reads took their snapshots before either commit, and it swallows `BrokenBarrierError`. One live pass followed by one live RED confirms timing-dependent coverage. The Codex Worker still has no captured test execution due `_overlapped` import failure. Further implementation requires a fresh Worker path and an explicit decision to use Coordinator RED evidence or first harden the test harness.

## Owner-approved isolated runtime retry (2026-11-02)

- Owner approved `.team/tasks/CHPMIS-015-F7-local-postgres-provisioning-proposal.md`: a separate synthetic PostgreSQL 17 runtime, loopback port `55432`, unique Compose project/volume, no image pull, and a short-lived launcher that keeps the credential out of repo/chat/logs and injects it only into the Codex Worker process.
- The next fresh Worker must run the exact focused RED command above as its first shell command. If it skips or fails to produce the expected live duplicate-grant RED, it must stop immediately before further reads or edits.

## Owner-approved temporary Codex sandbox networking (2026-11-02)

- After the Codex CLI Worker and a no-DB Python smoke command failed before DB access with `WinError 10106` importing `_overlapped`, the owner approved one temporary per-run `sandbox_workspace_write.network_access=true` override for a fresh F7 Worker.
- Keep `--sandbox workspace-write`; do not use full-access mode. Do not change persistent Codex configuration. The launcher includes only `TEST_DATABASE_URL` in the Worker shell environment allowlist. The Worker remains bound by this card: exact first live RED command; stop immediately without extra commands/reads/edits on skip or absent expected RED; otherwise only the approved two-file scope and listed verification commands.

### Temporary network override outcome

- Fresh Codex Worker kept `--sandbox workspace-write` and received the owner-approved per-run `sandbox_workspace_write.network_access=true` override. Its exact first focused command still exited 1 during pytest plugin import with `OSError: [WinError 10106]` importing `_overlapped` through `anyio`; pytest collection and database access did not begin. It stopped without additional commands, reads, or edits. The override did not solve the runtime failure, and no persistent configuration was changed.
- Coordinator's bounded diagnostic run captured the expected live RED (`1 failed, 5 deselected`, two distinct approval requests both returned HTTP 200). The owner later explicitly authorized that evidence as the entry gate for the fresh implementation Worker; see the approval section below.

## Owner-approved RED gate substitution (2026-11-02)

- Owner explicitly approved using the Coordinator-captured live RED as the entry gate for a fresh implementation Worker, because the Worker cannot initialize `_overlapped` even with the approved temporary network override. Evidence: exact focused test from `backend/` exited 1 with `1 failed, 5 deselected, 2 warnings in 6.05s`; assertion showed two distinct approval requests both returned HTTP 200.
- For this fresh run, do not retry the blocked Worker RED command. The Worker must read the diagnosis and approved proposal, follow TDD, modify only `backend/app/auth/routes.py` and `backend/tests/test_postgresql.py`, and run only the listed verification commands that work in its environment. If a command fails at `_overlapped` import, record exact failure and stop; do not widen sandbox or run additional diagnostics. Coordinator will run the assigned live PostgreSQL verification after Worker edits using the approved synthetic runtime. All other task boundaries remain unchanged.

## Fresh Worker result (2026-11-02)

- Worker `/root/chpmis015_f7_worker_retry` used the authorized Coordinator RED gate and modified only the two approved files. It added `.with_for_update()` to the target `User` lookup before the existing-role query; the F6 race test uses a `chpmis_015_f6_` database namespace and asserts the approved status/role/request/session outcomes.
- Worker focused PostgreSQL command: exit 0, `1 skipped, 5 deselected, 2 warnings in 24.55s` because `TEST_DATABASE_URL` was not available in its process. PostgreSQL module: exit 0, `6 skipped, 2 warnings in 2.63s`. Worker full suite initially had a failed attempt caused by a PowerShell path error and then reported `137 passed, 6 skipped, 16 setup errors` due access denial to a user temp directory. Those are Worker-process results only; Coordinator reran the required full suite with the approved runtime below.
- Final Worker static checks: Ruff check exit 0; Ruff format check passed after a formatting correction; scoped `git diff --check` exit 0. No commit.
- Coordinator post-edit live verification: focused case `1 passed, 5 deselected, 2 warnings in 2.69s` (exit 0); PostgreSQL module `6 passed, 9 warnings in 5.01s` (exit 0); full backend suite `159 passed, 9 warnings in 12.46s` (exit 0); Ruff check exit 0; Ruff format check exit 0; scoped `git diff --check` exit 0. No PostgreSQL skips.
- Independent Hermes Reviewer card `t_3f1a5b25`, session `20261102_141448_e86ed6`, APPROVED with 0 P1/P2/P3 findings. OpenCode verifier session is still `NOT_VERIFIED` pending a final verdict; session `ses_e64ec5c0cffePKAwFK0ryX244T` was created but the role-run helper did not record completion.
