# CHPMIS-019-F1-R1 — Independent Frontend Review

- **Task ID:** CHPMIS-019-F1-R1
- **Role:** Hermes Reviewer (read-only)
- **Status:** COMPLETE — APPROVED (0 P1/P2/P3); overall implementation task remains IN REVIEW because OpenCode could not run.
- **Scope:** Review only the final CHPMIS-019-F1 diff and worker report in the named allowlist. Do not edit or format files.
- **Definition of Done:** Confirm that the API error formatter handles FastAPI string/array/object/malformed details without rendering objects or echoing validation `input`; and that mutation refresh and audit pagination cannot write project A state after B is selected. Inspect whether `selectedProjectIdRef` updates early enough relative to every project-selection path, all relevant async writes/errors, and whether test cases exercise real deferred completion order. Confirm no unrelated auth, workflow, or due-date behavior changed. Record concrete findings and limitations.
- **Requirement trace:** `.team/tasks/CHPMIS-019-F1-frontend-stale-response-and-validation-errors.md`, mission §6.
- **Evidence:** Coordinator independently ran focused Vitest 13 passed, full frontend suite 26 passed, lint exit 0, build exit 0, and scoped diff check exit 0. OpenCode verifier is NOT_VERIFIED because the configured default route had no usable provider key; see `.team/tasks/CHPMIS-019-F1-opencode-readonly-verification.md`.
- **Prompt template:** Not applicable; read-only Reviewer.

## Hermes card closing contract

ROLE: reviewer (read-only). Inspect the scoped diff, worker report, task pack, and tests. Do not edit implementation. Finish with exactly one of `kanban_complete(result=...)`, `kanban_request_changes(reason=...)`, or `kanban_block(reason=...)`. Cite concrete file/line evidence and state the OpenCode limitation accurately.

## Reviewer result (Coordinator capture)

- **Hermes card:** `t_281989f0`, run #100, session `20261101_232016_96518d`.
- **Verdict:** APPROVED with 0 P1/P2/P3 findings.
- **Evidence:** Reviewer independently ran the focused 13-test suite, full frontend suite (26 tests), lint, build, and diff check; all exited 0. It confirmed the formatter at `frontend/src/lib/apiError.ts:59` avoids rendering non-string values and ignores validation `input`; it confirmed deferred project A mutation-refresh and audit-pagination tests at `frontend/src/ProjectWorkbench.test.tsx` cover out-of-order responses; and it reviewed the selection-ref guards in `frontend/src/components/ProjectWorkbench.tsx:227-268,373-384`.
- **Limit:** OpenCode run `2026-11-01T16-16-21-verifier-chpmis-019-f1-read-only-verification-898e` remains NOT_VERIFIED: no usable provider key, no checks ran. Its status is not represented as a pass. The task remains IN REVIEW until the configured OpenCode route becomes usable or the project owner explicitly changes routing.
