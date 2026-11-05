# CHPMIS-018-F1-R2-W1 — Document RED-Only Gate Limitation

## Task identity

- **Task ID:** CHPMIS-018-F1-R2-W1
- **Role:** OpenCode test-only Worker (`role-worker`)
- **Status:** READY — scoped response to Reviewer P2-1.
- **Trace:** CHPMIS-018-F1 task pack; mission §6; OpenCode Reviewer run `2026-11-03T02-50-37-reviewer-chpmis-018-f1-independent-read-only-revi-5743`, finding P2-1.
- **Prompt template:** prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template. Modernized for this bounded report-only correction.

## Objective

Address Reviewer P2-1 by adding a concise limitation to Section 8 of `.team/tasks/CHPMIS-018-F1-worker-report.md`: the `update_gate_waiters == 2` Stage 2 assertion is specific to reproducing the current lost update, and this deterministic barrier test is not expected to pass after a row-lock fix because the second task SELECT may block before both SELECTs can pass the barrier. State that the test is a RED reproducer, not a green regression test for a future fix.

## Scope and boundaries

- Modify only `.team/tasks/CHPMIS-018-F1-worker-report.md`, by appending the limitation to Section 8.
- Do not modify product code, `backend/tests/test_postgresql.py`, task semantics, task packs other than this report, or the Reviewer finding.
- Do not add a proposed fix or claim the lost update has been fixed.
- Preserve all synthetic databases; do not access credentials, environments, services, or external providers.
- Do not commit.

## Verification and evidence

From repository root, run the existing scoped whitespace check:

1. `git diff --check -- .team/tasks/CHPMIS-018-F1-worker-report.md`

Report the exact output and exit code, changed-path status, and requirement trace. If the command is denied or unavailable, report `NOT_VERIFIED`; do not substitute another command.

## Definition of Done

- Section 8 clearly discloses why the deterministic two-stage barrier is RED-specific under a row-lock fix.
- No file other than the Worker report is modified by this task.
- The exact assigned check result is recorded, and the change is ready for a second independent OpenCode Reviewer pass.

## Modernized prompt

“Using the cited Feature coding template, act as the CHPMIS-018-F1 scoped Worker. Address Reviewer P2-1 only by appending the row-lock/barrier limitation to Section 8 of the Worker report. Edit no other path, make no product or test changes, preserve all databases, run only the assigned `git diff --check` command, report exact scope and result, and do not commit.”
