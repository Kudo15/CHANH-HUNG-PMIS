# CHPMIS-018-F2 — Proposed concurrency correction

**Status: OWNER APPROVED — bounded workflow behavior and Worker scope, 2026-11-03.** The owner also approved using the recorded Worker RED as starting evidence while F1-T1 remains BLOCKED / independently NOT_VERIFIED. This does not authorize a role permission exception, a service lifecycle change, or a change to the F1-T1 decision.

## Problem and evidence

CHPMIS-018-F1's Worker reported that two concurrent Project Manager requests from the same `in_progress` state both returned HTTP 200, overwrote one task status, and recorded two audit events with the same stale before-state. OpenCode R2 approved the static reproduction review; its independent Tester could not run the live test. The live RED remains Worker-reported, **NOT_VERIFIED independently**. Details: `.team/tasks/CHPMIS-018-F1-worker-report.md` and `.team/tasks/CHPMIS-018-F1-opencode-tester.md`.

## Proposed behavior for owner decision

For concurrent transitions of one task, serialize the status decision within the existing database transaction. The second request must evaluate the latest committed status against the existing approved transition graph. Preserve the current 400 invalid-transition or terminal-state response where the second transition is no longer allowed. If both transitions are valid in sequence, preserve the existing graph and record each accepted transition with its actual before and after status. Do not add a new conflict response or silently overwrite an accepted transition.

For the reported `in_progress → done` versus `in_progress → cancelled` case, the expected result is one 200, one 400, one transition audit event, and a final status matching the accepted transition.

## Proposed implementation boundary

- Worker changes limited to `backend/app/projects/service.py` and `backend/tests/test_postgresql.py`, plus an append-only task report. No schema, migration, dependency, authorization policy, transition graph, other API behavior, or unrelated files change.
- Candidate mechanism: acquire a PostgreSQL row lock on the target task in the current transaction after the appropriate access checks, refresh the ORM state before evaluating the transition, and keep the status update and audit insertion atomic. The exact placement must preserve existing non-disclosure and authorization behavior; the Worker must stop if this cannot be accomplished within scope.
- The existing F1 two-stage barrier is a RED reproducer and cannot serve as a green row-lock regression. Adapt or isolate it without erasing its historical evidence; add a bounded PostgreSQL concurrency regression that works with serialization and checks HTTP outcomes, final status, and audit values. Preserve existing administrative approval concurrency coverage. Use fresh synthetic databases and preserve them.
- Use TDD, run the focused live PostgreSQL regression and relevant existing repository backend checks, record exact exits/skips and request a separate OpenCode read-only review. The final task pack must identify exact commands and cite a real prompt template retrieved through the installed prompt-search skill before any Worker dispatch.

## Prompt preparation

On 2026-11-03, the installed `prompt-lookup` skill searched for and retrieved prompts.chat [Feature coding template](https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa), Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`. Proposed adaptation: act as the bounded Python/FastAPI/SQLAlchemy Worker; first build a deterministic PostgreSQL concurrency regression preserving the existing RED evidence, implement the owner-approved serialization within the stated files, preserve authorization and response semantics, run the final task's exact checks, and report evidence without committing. The template's general README-update instruction does not expand this proposal's allowlist. The final task pack and owner approval are still required before dispatch.

## Decision needed

Owner selected **“Duyệt đề xuất và dùng RED đã ghi”** on 2026-11-03. The missing independent F1-T1 rerun remains NOT_VERIFIED. The owner separately selected **“Cho phép môi trường F2”** for one synthetic PostgreSQL 17 container on a random loopback port, process-generated password passed by environment, and preserved container/volume/databases. No F1-T1 exception or role permission change is approved. Independent testing/review required by the final task pack remains necessary for closure.
