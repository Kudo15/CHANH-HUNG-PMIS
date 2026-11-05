# OPENCODE-SKILL-001 — Repair and smoke-test OpenCode role-agent skill

## Identity and status

- **Task ID:** OPENCODE-SKILL-001
- **Role:** Coordinator / Skill Maintainer; one OpenCode Worker smoke run.
- **Status:** COMPLETE
- **Trace:** User request on 2026-11-05 to update the local OpenCode role-agent skill and run one task through it.
- **Required reads:** `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this pack, and `docs/agent-skills/opencode-role-agents/SKILL.md` plus its CLI contract and driver.

## Objective

Update the project copy of `opencode-role-agents` so this Windows PC's npm-installed OpenCode CLI is resolved to its native executable, agent installation cannot silently overwrite an unknown global role file, and malformed timeout values are rejected before dispatch. Make the skill discoverable through `.agents/skills`. Then run exactly one bounded, synthetic OpenCode Worker smoke task and confirm its session is listed for the PMIS project in the shared service.

## Scope

Allowed changes:

- `docs/agent-skills/opencode-role-agents/**`
- `.agents/skills/opencode-role-agents/**` (installed mirror of the source skill)
- `docs/agent-skills/SKILLS-PORTABILITY.md`
- `.team/tasks/OPENCODE-SKILL-001.md`
- `.team/ledger.md`
- `TASKS.md`

No product source, tests, application configuration, credentials, OpenCode service configuration, or unrelated skills. Preserve all existing dirty/untracked work. Do not use Computer Use.

## Prompt template

- **Worker smoke prompt source:** prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, already retrieved via the project's `prompt-lookup` skill and adapted in `.team/tasks/CHPMIS-024-opencode-role-smoke.md`.
- **Adaptation:** one response-only synthetic Python clamp function task. No project files, tools, edits, or real data. Use the configured default model/provider; do not override the model.
- The smoke dispatch is not an implementation Worker assignment and may not edit project files.

## Acceptance criteria

- [x] OpenCode CLI discovery supports this PC's npm install by selecting `node_modules/@opencode/cli/bin/opencode.exe`, and never tries to spawn the extensionless npm shim on Windows.
- [x] Existing unmarked/newer global agent files are preserved and cause a clear block unless the user explicitly passes `--force-agents`; only recognized older skill-owned versions auto-upgrade.
- [x] Non-numeric, non-finite, zero, or negative `--timeout` values fail as usage errors before ledger/session side effects.
- [x] Documentation matches the resolver, installed v2.2.5 CLI, role-agent overwrite behavior, timeout policy, and GUI visibility evidence.
- [x] Node built-in tests for the changed helper logic pass; `node --check` passes for the driver.
- [x] One OpenCode Worker smoke task returns the expected toy result; driver reports `gui_visible: true`; session ID is shown by the shared service `session list` check.
- [x] No project files were changed by the role run. Exact command, exit code, session/run IDs, model/provider metadata, and limitations are recorded below.

## Execution evidence (2026-11-05)

- **Static/unit checks:** `node --test docs/agent-skills/opencode-role-agents/scripts/opencode-cli-resolver.test.mjs docs/agent-skills/opencode-role-agents/scripts/agent-installer.test.mjs docs/agent-skills/opencode-role-agents/scripts/role-task-options.test.mjs docs/agent-skills/opencode-role-agents/scripts/opencode-role-task.test.mjs` — 12 passed, 0 failed, exit 0. `node --check docs/agent-skills/opencode-role-agents/scripts/opencode-role-task.mjs` — exit 0.
- **Preflight:** `node docs/agent-skills/opencode-role-agents/scripts/opencode-role-task.mjs --status` with `OPENCODE_CLI_BIN=C:\Users\AZAI\AppData\Roaming\npm\node_modules\@opencode\cli\bin\opencode.exe` — exit 0; CLI v2.2.5, service `http://127.0.0.1:28894`, service pid 6320 alive, OpenCode Desktop running, API 200.
- **Dry-run:** Same driver with the smoke arguments and `--dry-run` — exit 0; printed the exact command/body and did not create ledger/run files (also asserted by test).
- **Single authorized task command:** `$env:OPENCODE_CLI_BIN = 'C:\Users\AZAI\AppData\Roaming\npm\node_modules\@opencode\cli\bin\opencode.exe'; node docs/agent-skills/opencode-role-agents/scripts/opencode-role-task.mjs --title "OPENCODE-SKILL-001 CLI Worker smoke" --role worker --repo "C:\Users\AZAI\Desktop\CHANH HUNG PMIS" --timeout 180 --body "Role: Worker. Solve this synthetic toy task only: write a Python function clamp_score(value) that clamps to [0, 100], and show outputs for -2, 42, and 101. Do not inspect or modify project files, use tools, or handle real data. Return concise code and examples." --json` — exit 0, status `done`, outcome `succeeded`, `ROLE_RESULT: done`.
- **Session/run:** run `2026-11-05T02-35-00-worker-opencode-skill-001-cli-worker-smoke-20ef`; session `ses_e5670b683ffet88NxXW2dfGX85`; agent `role-worker`; title `worker: OPENCODE-SKILL-001 CLI Worker smoke`; `gui_visible: true`; session directory matches the PMIS repo. GUI hint: OpenCode Desktop → project `C:/Users/AZAI/Desktop/CHANH HUNG PMIS` → that session title.
- **Result:** Worker returned `clamp_score` with outputs `0, 42, 100` for inputs `-2, 42, 101`; summary confirms no project files or tools were touched. Model was not exposed (`model_used: null`, no model override); cost `$0`, input 6421/output 312/reasoning 297 tokens.
- **Limitations:** GUI visibility is evidenced by shared-service session listing and matching exported project directory; no Computer Use inspection was performed. The task was a response-only smoke, not a live code execution test or product code review.

## Baseline evidence before edits

- `node docs/agent-skills/opencode-role-agents/scripts/opencode-role-task.mjs --status` failed exit 1: resolver selected `C:\Users\AZAI\AppData\Roaming\npm\opencode`, and `spawnSync` returned `ENOENT`.
- With `OPENCODE_CLI_BIN` set to `C:\Users\AZAI\AppData\Roaming\npm\node_modules\@opencode\cli\bin\opencode.exe`, the same preflight passed exit 0: v2.2.5, service `http://127.0.0.1:28894`, Desktop running, API 200.

## Human Gates and safety

- User explicitly requested one OpenCode task on 2026-11-05; this authorizes one configured-provider smoke run. No model/provider override, fan-out, or second run.
- Use the default shared service; never `--standalone` or a private server.
- Do not inspect credential files or print secrets. Do not overwrite role agents without an explicit `--force-agents` option.
- Role task body is synthetic and explicitly prohibits tools/files; no real agency data.

## Definition of Done

- Skill source and discoverable mirror are updated within scope.
- Assigned local static/unit checks have exact output and exit codes.
- The single CLI smoke task and GUI-listing evidence are recorded; if any check is unavailable, mark it `NOT_VERIFIED` and do not claim completion.
- `TASKS.md` and `.team/ledger.md` record the outcome and limits.
