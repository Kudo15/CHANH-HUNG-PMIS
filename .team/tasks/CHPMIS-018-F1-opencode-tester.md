# CHPMIS-018-F1-T1 — OpenCode Independent Tester

## Task identity

- **Task ID:** CHPMIS-018-F1-T1
- **Role:** OpenCode read-only Tester (`role-verifier`)
- **Status:** BLOCKED / OWNER DECISION — The owner chose to keep T1 blocked rather than authorize the proposed task-specific verifier and new PostgreSQL service. No retry has been dispatched. Live RED remains NOT_VERIFIED independently; await further owner direction before any new T1 dispatch.
- **Trace:** CHPMIS-018-F1 task pack; mission §6; approved Human Gate 3 task-transition graph.

## Objective

Independently verify the test-only lost-update reproduction and its assigned checks. The Worker reported a RED result: both concurrent `in_progress` transitions were accepted with HTTP 200, and both audit rows had stale `before.status = in_progress`. RED is the expected defect evidence for this reproduction task; report it as a reproduced defect, never as a passing serialized-behavior test.

## Scope and boundaries

- Read-only inspection and verification only. Do not edit product code, tests, reports, task packs, or configuration.
- Inspect only `backend/tests/test_postgresql.py`, `.team/tasks/CHPMIS-018-F1-worker-report.md`, and this task's requirements.
- Use only existing process-local synthetic loopback PostgreSQL settings. Never print environment values or credentials, access external providers, start services, drop/reset databases, or clean up any synthetic records.
- If the required PostgreSQL context is unavailable, record `NOT_VERIFIED`; a skipped PostgreSQL test is not a pass. Do not substitute another interpreter, database, or service.

## Assigned verification

From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k concurrent_task_transition_serialized`
2. `.venv\Scripts\ruff.exe check tests/test_postgresql.py`
3. `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py`

From repository root:

4. `git diff --check -- backend/tests/test_postgresql.py .team/tasks/CHPMIS-018-F1-worker-report.md`

Record exact output, exit codes, skip count, the synthetic `018_f1` database name if the test executes, and preservation evidence. Do not inspect or print connection strings. Confirm the existing `test_postgresql_concurrent_approval_serialized` remains unchanged in the diff.

## Completed Tester result

- Focused pytest `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k concurrent_task_transition_serialized`: **NOT_VERIFIED**; denied by the OpenCode shell allowlist before execution; no test output, process exit, or skip count.
- Ruff check `.venv\Scripts\ruff.exe check tests/test_postgresql.py`: **NOT_VERIFIED**; denied before execution; no process exit.
- Ruff format `.venv\Scripts\ruff.exe format --check tests/test_postgresql.py`: **NOT_VERIFIED**; denied before execution; no process exit.
- Scoped diff check `git diff --check -- backend/tests/test_postgresql.py .team/tasks/CHPMIS-018-F1-worker-report.md`: **NOT_VERIFIED** as an assigned command; denied before execution; no process exit.
- The Tester separately reports static scope inspection: test diff is additive `300/0`; existing approval concurrency test is unchanged; whitespace check on the test file was clean; no files were modified by Tester. These are Tester-reported static observations, not live PostgreSQL evidence.
- Role summary: “Ran read-only static checks (git status/diff numstat/diff --check test file: 300/0 additive, approval test unchanged, whitespace clean) but all four assigned verification commands were denied by the shell allowlist and the process-local PostgreSQL settings are absent, so the live RED result is NOT_VERIFIED, not independently reproduced.”
- Run: `2026-11-03T02-38-33-verifier-chpmis-018-f1-independent-postgresql-tes-3716`; session `ses_e60ba333affeReBshIBQpLKvEw`; GUI listed; model unavailable in record (`-`); cost `$0`; tokens in `156689`, out `3763`, cache-read `518400`; run directory `C:\Users\ANHVU\.opencode\role-runs\runs\2026-11-03T02-38-33-verifier-chpmis-018-f1-independent-postgresql-tes-3716`.

## Owner-requested fresh T1 retry — environment prerequisite

- Owner selected **run T1 again in an allowed environment** after Reviewer R2's completion gate.
- Coordinator checked only executable presence and setting-name presence from `backend/` (no values read or printed): `.venv\Scripts\python.exe` present; `.venv\Scripts\ruff.exe` present; `TEST_DATABASE_URL` absent; `DATABASE_URL` absent.
- Installed OpenCode `role-verifier` prompt has `bash: "*": deny` with explicit allow rules for command prefixes such as `python *`, `pytest *`, and `git *`; it does not allow `.venv\Scripts\python.exe` or `.venv\Scripts\ruff.exe` command forms. R1 confirmed all four assigned command invocations are denied before execution. Do not widen/bypass this role policy or substitute another interpreter/command.
- No fresh run was dispatched because the same denied commands and missing PostgreSQL context would produce no verification evidence. Fresh T1 is pending an OpenCode verifier environment that permits the exact assigned commands and receives process-local synthetic loopback PostgreSQL settings without exposing their values.
- OpenCode DIAG1 subsequently confirmed a harmless environment marker reaches a verifier shell (`PRESENT`, exit 0). This is environment evidence only, not T1 verification. The owner chose to keep T1 blocked and did not authorize the scoped exception in `.team/tasks/CHPMIS-018-F1-T1-environment-proposal.md`.

## Definition of Done

- Exact results and exit codes for all four assigned commands are reported.
- The result distinguishes expected RED evidence from a pass and reports `NOT_VERIFIED` if the live test skips or cannot run.
- Scope and requirement trace are stated; no files are modified.
- Report completion in the OpenCode role result and project ledger; do not commit.
