# Task Pack — CHPMIS-008-R1 Independent Reviewer

- **Task ID:** CHPMIS-008-R1.
- **Role:** Independent Reviewer, Hermes CLI Kanban `role=reviewer`.
- **Scope:** Read CHPMIS-008 pack/plan, inspect only its allowed test and its evidence, review correctness, security semantics, negative assertions, and scope. Do not edit.
- **Prompt template:** Senior Code Reviewer (severity-ranked), prompts.chat ID `cmv9n79m30005ku060pzornri`, retrieved/adapted in this task pack.
- **Workspace:** same repository directory; separate Hermes Reviewer card after Worker and OpenCode Tester finish.
- **DoD:** verdict `APPROVED` or `CHANGES_REQUESTED`; findings include priority and exact `file:line`, impact, correction direction; record test evidence and baseline limitation.
- **Trace:** AC-10, approved HG2 policy, CHPMIS-008 plan and test.
- **Verification state:** OpenCode Tester completed as `blocked` because shell permission denied before both pytest commands; independently executed pytest evidence is `NOT_VERIFIED`. Review the source assertions and Worker evidence statically; do not attempt shell/test workarounds.

Review especially: matching synthetic department values, no explicit membership row, 404/non-disclosure on reads, empty list/dashboard, valid-CSRF denied writes, unchanged persisted state, and no denied-write audit events. Do not claim production IdP/database or legal verification.

## Actual review result
- Hermes card `t_e1d1d599`, run #28, profile `default`, reviewer session `20261030_172626_500a95`; status `done`.
- Verdict `APPROVED`, zero P1/P2/P3 findings. Two P4 informational notes: response bodies are not asserted; audit-event absence filters by action globally, stricter than required in this isolated SQLite setup.
- Reviewer verified assertions statically. OpenCode Tester execution remains `NOT_VERIFIED` due permission denial; Worker results are not represented as independent Tester evidence.
