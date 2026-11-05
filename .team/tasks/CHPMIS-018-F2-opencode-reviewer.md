# CHPMIS-018-F2-R1 — Independent OpenCode Reviewer

- **Role:** OpenCode independent read-only Reviewer; **trace:** CHPMIS-018-F2, mission §6, HG3.
- **Session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, `.team/tasks/CHPMIS-018-F2-task-transition-worker.md`, its Worker report, the completed Tester evidence, `docs/MISSION.md` and `ACCEPTANCE.md`; report each read.
- **Scope:** Review the F2 diff in `backend/app/projects/service.py` and `backend/tests/test_postgresql.py`, the owner-approved behavior, existing authorization/non-disclosure and transition graph, atomic status/audit semantics, lock-compatible regression, and recorded verification. Do not change files, inspect credentials, access databases or services, modify permissions, or use other agents.
- **DoD:** Return `APPROVED` or `CHANGES_REQUESTED` with actionable file/line and severity for findings. Check that the final regression is bounded and will not deadlock on the selected lock design; that the old F1 RED-only evidence remains accurate; and that any Tester denial/skips stay explicitly NOT_VERIFIED. Do not close the task yourself.
- **Specific evidence question:** Check whether the `before_cursor_execute` barrier establishes that both initial SELECTs have actually read the prior status, or only that both have reached the point before execution. Assess whether a sequential execution could pass the final regression and whether the report's deterministic-read claim is supported. The Worker also reports creating a diagnostic helper in OS temp: compare this with the task's write allowlist and report any scope deviation separately from product correctness.

SUMMARY: <one line>
ROLE_RESULT: <done|review|blocked>

## R1 outcome — 2026-11-03

Driver exceeded 1200 seconds; role ledger records timeout / exit 1. The same GUI session `ses_e5fd27596ffegAzNmGUjW0yL6V` later finished `ROLE_RESULT: review`, **CHANGES_REQUESTED**, with 2 P2 and 2 P3. Final-message model `auto:coding`, provider `openai-completions`, cost 0, tokens input 3249 / output 2695 / cache-read 116800 (not session total). Reviewer reports all required reads; read-only, no tests or database access.

- P2-1: `before_cursor_execute` on the initial non-locking SELECT proves only both threads arrived before execution, not that both have read the prior state. A serialized execution can satisfy the test, so the docstring/report overstate its evidence. Reviewer suggests wording-only correction and argues requiring both reads would make the test flaky. Coordinator agrees with the diagnosis but not that conclusion: a bounded barrier *before the subsequent lock SELECT*, after each request's initial task read has returned, can deliberately select the overlapping interleaving. A test that controls this interleaving does not reject ordinary production scheduling. The approved objective calls for a concurrency regression, so a scoped Worker must strengthen the gate and report its exact guarantees; new review is required.
- P2-2: Worker created the supplementary `C:\Users\ANHVU\AppData\Local\Temp\opencode\chpmis018_f2_diag.py` outside the strict write allowlist. This is a recorded process deviation, separate from product correctness; no cleanup is authorized or performed. The supplementary database queries do not replace mandated checks.
- P3-1: Worker report service-file diff count says 23 insertions / 1 deletion; Reviewer observed 22 insertions / 1 deletion (23 changed lines). Correct the report.
- P3-2: Worker disclosed supplementary full-suite and `--collect-only` commands outside the assigned list; record as minor command-scope deviations rather than recategorizing them as assigned checks.

Reviewer assessed row-lock refresh, graph/non-disclosure preservation, and atomic audit as sound in static review, and confirmed the existing gate is bounded and F1's RED-only report remains intact. **Factual correction:** the Reviewer repeatedly says all six Tester commands were denied; the Tester record establishes only command 1 was denied, while commands 2–6 were not attempted by the stop rule. All six remain NOT_VERIFIED. No owner waiver of the Tester requirement has been granted for F2.
