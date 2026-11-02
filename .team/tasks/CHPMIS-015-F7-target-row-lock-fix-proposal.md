# CHPMIS-015-F7 — Serialize Role Decisions by Locking the Target User

## Approval status

- **Task ID:** CHPMIS-015-F7
- **Status:** `COMPLETE — OWNER ACCEPTED HERMES REVIEW + COORDINATOR LIVE CHECKS; OPENCODE NOT_VERIFIED AND WAIVED FOR CLOSURE` (2026-11-02). The fresh Worker used the owner-approved Coordinator RED gate and changed only the approved two files. Coordinator's recorded focused PostgreSQL test (`1 passed, 5 deselected`), PostgreSQL module (`6 passed`), full backend suite (`159 passed`), Ruff checks, and scoped diff check all passed with zero skips. Independent Hermes review is APPROVED with zero findings. OpenCode returned no final verdict; the owner explicitly chose to close using Hermes plus the recorded live checks. A later closure-session rerun of the focused PostgreSQL test skipped (`1 skipped`) because the process-local database context was unavailable, so that rerun is `NOT_VERIFIED` and is not counted as passing evidence. See `.team/tasks/CHPMIS-015-F7-codex-worker.md` and `.team/tasks/CHPMIS-015-F7-independent-review.md`.
- **Human Gate source:** Repository `AGENTS.md` requires explicit approval for authentication/authorization policy or important approval-workflow changes. Although the proposed change adds no permission, it changes the approval transaction's concurrency behavior.
- **Parent:** CHPMIS-015-F6 live distinct-request PostgreSQL finding.
- **Trace:** Mission §6; `.team/tasks/CHPMIS-015-F6-coordinator-evidence.md`.

## Finding

Two distinct pending `grant` requests for the same synthetic target can both return HTTP 200 and commit two canonical `system_admin` rows. The same-request lock does not serialize different request IDs. Coordinator read-only checks of four preserved synthetic databases found two active role rows, two approved requests, and one revoked target session in each.

## Exact proposed scope

Under the approved scope, assign a Codex Worker to change only:

- `backend/app/auth/routes.py`
- `backend/tests/test_postgresql.py`

Proposed correction: after locking and validating the approval request and before checking `existing_grant`, acquire a `SELECT ... FOR UPDATE` lock on the existing target `User` row in the same transaction. This serializes grant/revoke decisions that target that same user; the second distinct grant should observe the committed role and return the existing 409 conflict. Preserve request-row locking, dual-control and canonical authority checks, bootstrap behavior, session revocation, audit fields, and API response behavior.

The regression test should require exactly one 200 and one 409, one active canonical role, one approved request with the other request still pending, and target-session revocation. Give F6's test its own synthetic database namespace (for example `chpmis_015_f6_distinct_target_<uuid>`) so its runtime records are distinguishable. Preserve all existing databases and tests.

## Explicit exclusions

No migration, unique constraint, schema/model change, data cleanup, legacy-role conversion, permission change, bootstrap change, identity-provider change, deployment, or production/staging access. If the Worker finds target-row locking insufficient or proposes broader workflow/schema behavior, stop and request a new Human Gate decision.

## Verification after approval

Run from `backend/` with process-local synthetic loopback PostgreSQL settings:

- First rerun the current F6 test and record its RED result before any edits.
- `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py -k distinct_requests_same_target`
- `.venv\Scripts\python.exe -m pytest -q tests/test_postgresql.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check app/auth/routes.py tests/test_postgresql.py`
- `.venv\Scripts\ruff.exe format --check app/auth/routes.py tests/test_postgresql.py`
- From repository root: `git diff --check -- backend/app/auth/routes.py backend/tests/test_postgresql.py`

Coordinator-owned live PostgreSQL verification must report zero skips. The original gate also required OpenCode read-only verification when available and an independent Hermes Reviewer on the final diff. Owner's explicit closure decision on 2026-11-02 accepts the recorded Coordinator live checks and Hermes approval for this task despite OpenCode having no verdict. Keep OpenCode `NOT_VERIFIED`; this owner decision waives it as a closure blocker and does not convert it to a pass.

## Prompt template for the Worker

- Real template retrieved through installed prompt-lookup: prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template.
- Modernized Worker prompt: “Act as the CHPMIS-015-F7 backend authorization Worker. After the exact Human Gate approval is recorded, first rerun the F6 distinct-request PostgreSQL test and record RED before editing. Make the smallest transaction-only correction by serializing decisions on the target user's database row before the existing-role check. Modify only `backend/app/auth/routes.py` and `backend/tests/test_postgresql.py`. Preserve canonical decision authority, dual control, same-request locking, bootstrap behavior, session revocation, audit fields, API responses, and all schema. Give F6 isolated `chpmis_015_f6_` synthetic databases; preserve every database and never print credentials. If this needs a schema/constraint or broader workflow change, stop for another approval. Run assigned checks, record exact commands/results/exits/skips, and request independent review; do not commit.”

## Approval request

Owner approval was recorded on 2026-11-02 for the exact route-and-test scope and target-user row-lock approach above. No schema, migration, or broader workflow changes are authorized.

## Updated verification gate (2026-11-02)

Owner separately approved the Coordinator-captured RED as the gate for a fresh Worker, because the Worker fails before pytest collection with `WinError 10106` even with a temporary per-run network override. Coordinator RED evidence: exact focused test, exit 1, `1 failed, 5 deselected, 2 warnings in 6.05s`, showing two distinct approval requests both HTTP 200. The Worker must still follow TDD in the approved two-file scope. Coordinator owns post-edit live PostgreSQL verification; a skip or inability to run remains `NOT_VERIFIED`.
