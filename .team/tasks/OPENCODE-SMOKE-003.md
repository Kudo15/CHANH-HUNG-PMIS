# Task Pack — OPENCODE-SMOKE-003 OpenCode Tester Route Smoke

## Task ID and role
- Task ID: OPENCODE-SMOKE-003.
- Role: Independent Tester / Verifier (OpenCode `role-verifier`).
- State: COMPLETE — focused read-only test passed under OpenCode `role-verifier` after model configuration update.
- Trace: `.team/routing.json` Tester route; `frontend/src/App.test.tsx` overdue behavior test.

## Objective and boundaries
Confirm that the newly configured OpenCode Tester route can execute one existing, focused unit test and return a trace. This is a routing smoke, not a product change or full verification.

- Read-only: do not edit source, tests, docs, configs, lockfiles, or generated assets.
- Do not install dependencies, access production, start services, or run additional checks.
- Execute only: `npm --prefix frontend run test -- --run -t "calculates isTaskOverdue with frozen time and terminal exclusion"` from the repository root.
- If that exact test cannot be selected or the command would require a change, stop and report `ROLE_RESULT: blocked`.
- Do not pass an explicit model override; inherit the active OpenCode configured default.

## Prior attempt and retry instructions
- Prior driver run `2026-10-30T09-38-31-verifier-opencode-smoke-003-focused-read-only-tes-8275` failed before test execution because the configured model was unavailable to the prior free-tier entitlement. The user now reports the model configuration was changed and explicitly authorizes this retry.
- Use the currently configured OpenCode default (no model override). If the same entitlement error occurs, stop and report blocked; do not substitute a model.
- The user explicitly authorized another retry after reporting a further model configuration change; this authorization supersedes the previous no-third-attempt note.

## Successful smoke result
- Run `2026-10-30T10-02-54-verifier-opencode-smoke-003-focused-read-only-tes-02b7`; session `ses_e73bcd2f7ffex6QJco8NfHDHbC`; `gui_visible=true`; OpenCode CLI `v2.2.2`, service `http://127.0.0.1:28894`.
- Exact command: `npm --prefix frontend run test -- --run -t "calculates isTaskOverdue with frozen time and terminal exclusion"` — 1 passed / 14 skipped, 1 file passed / 1 skipped; exit 0.
- Run outcome `done`; `model_requested=null`, `model_used=null` (configured default used, exact model ID not exposed); cost USD 0; tokens input/output/reasoning 14642 / 968 / 941.
- The two previous runs remain recorded failures before test execution. The verifier role is configured `edit: deny`; no source edits were reported. The frontend/backend trees were already untracked in the repository baseline, so their full contents are not independently diffable against Git.

## Retry result
- Run `2026-10-30T09-59-01-verifier-opencode-smoke-003-focused-read-only-tes-7b86`; session `ses_e73c05f71ffeA2CCfc9PVNlcFJ`; `gui_visible=true`.
- Exit 1 before the test command; exact error again: `Free tier users do not have access to this model.` `model_used=null`; driver recorded cost/tokens 0. The test was not executed. A further retry is permitted only on explicit user instruction; do not substitute a model.

## Prompt template and role contract
- Real template: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, searched/retrieved and adapted for read-only verification in `.team/tasks/CHPMIS-007-T1-test-evidence.md`.
- Apply the installed OpenCode `role-verifier` contract: edit denied, exact command/output/exit reported, no fixes.

## Definition of Done
- The exact selected test command and its exit code are reported.
- OpenCode returns machine-readable `SUMMARY` and `ROLE_RESULT` lines; driver trace includes run/session/model/cost/tokens/gui visibility as available.
- No product or task files are modified by the Tester.
- Coordinator records evidence and limits in `.team/ledger.md` and updates `.team/routing.json`.

## Requirement trace
- Routing objective: `.team/routing.json` → `tester`.
- Existing test target: `frontend/src/App.test.tsx` → `calculates isTaskOverdue with frozen time and terminal exclusion`.
- Existing project QA contract: `.team/CHARTER.md` → Tester / QA.
