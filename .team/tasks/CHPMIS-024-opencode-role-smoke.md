# CHPMIS-024 — OpenCode role smoke test

## Identity and scope

- **Task ID:** CHPMIS-024
- **Role:** Coordinator running three isolated OpenCode role-prompt sessions: Worker, read-only Tester, and independent Reviewer.
- **Objective:** Confirm that the configured OpenCode session can accept a role-scoped prompt and return a useful result for each role.
- **Scope:** Synthetic Python `clamp_score(value)` example only. No repository source, tests, credentials, tools, or files are provided to OpenCode.
- **Trace:** User request on 2026-11-04 to smoke test OpenCode as Worker/Tester/Reviewer. This is integration evidence only; it does not verify project code or replace any project's assigned Tester/Reviewer evidence.
- **Write scope:** This task pack, the corresponding TASKS.md row, and ledger entry only. No product code was changed.

## Prompt sources

- **Worker:** prompts.chat Feature coding template, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved through `.agents/skills/prompt-lookup/` and recorded in `.team/tasks/CHPMIS-018-F2-task-transition-worker.md`. Modernized to a response-only toy function task with explicit no-tools/no-files boundaries.
- **Tester:** The read-only Tester role shape from `.team/tasks/CHPMIS-018-F2-opencode-tester.md`, reduced to manually tracing five synthetic vectors without tools or files.
- **Reviewer:** The independent read-only Reviewer role shape from `.team/tasks/CHPMIS-018-F2-opencode-reviewer.md`, reduced to reviewing the toy function and reported vector results without tools or files.

## Definition of Done

- Each role receives a separate OpenCode session and returns its assigned output.
- The Worker function and Tester vectors are correct; the Reviewer returns an explicit verdict and identifies any concrete issue.
- No tools or files are used by the role sessions; no project files are changed.
- Record observed model/provider/session IDs and label any unavailable metadata `NOT_EXPOSED`.

## Results — 2026-11-04

OpenCode Desktop showed provider/model `FreeLLMAPI (free.vuhocai.shop) / Auto: coding`. Each session used the UI's `Default Project` under `C:\Users\AZAI\Documents`, not the PMIS repository. Model identity and billing metadata were not exposed.

| Role | Session | Result |
|---|---|---|
| Worker | `ses_e5bb08e7affe9oceuE3UxMn4cH` | Returned correct `clamp_score` implementation and boundary examples `-1 → 0`, `101 → 100`; displayed 14s. No tool use observed. |
| Tester | `ses_e5baf72c9ffe3m1cr4W33wtI4D` | Reported PASS for all five supplied vectors: -1, 0, 42, 100, 101. Trace was reasoning-only, not executed code; displayed 16s. No tool use observed. |
| Reviewer | `ses_e5baeb8e7ffdUkzn8lJa0zIlMj` | Returned APPROVED; confirmed the five results and noted `NaN` behavior/type documentation as non-blocking toy-example observations. Displayed 32s. No tool use observed. |

All three OpenCode role prompts completed. This verifies basic prompt/response connectivity through the configured provider, not CLI/API health, repository access, tool permissions, live code execution, or production readiness. The local `127.0.0.1:28894` UI returned HTTP 200 HTML at `/global/health`, so that route did not provide a JSON health result.

**Disposition:** COMPLETE for the isolated OpenCode role-prompt smoke test. Project-level Worker/Tester/Reviewer assignment still requires its own authorized task pack and evidence.
