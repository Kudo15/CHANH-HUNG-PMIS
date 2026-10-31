# Task Pack — HERMES-SMOKE-002 Hermes Worker Prompt Trace

## Task ID and role
- Task ID: HERMES-SMOKE-002
- Role: Hermes Worker dispatch smoke test; read-only
- Status: COMPLETE — card `t_075840fe`, run 24, terminal `done`, exit 0; exact marker received.

## Context
- User requested Worker/Reviewer routing through Hermes and all other roles through Codex's configured default model.
- Hermes CLI version and Kanban board preflight succeeded outside the sandbox. Gateway is stopped; dispatch must be explicit.
- Current repository contains uncommitted and untracked baseline files. The request used Hermes `scratch`, but the project-bound dispatcher created `.worktrees/t_075840fe`; the agent reported no repository access or file changes. The generated directory was inspected and removed after the run.
- Routing configuration is recorded in `.team/routing.json`; this card tests one prompt and reports the trace.

## Objective
Verify one Hermes default-profile Worker card can receive this exact bounded prompt, return a structured result through Kanban, and expose the available execution trace. Do not implement product changes or create files.

## Scope and boundaries
- Requested workspace: Hermes `scratch`; actual workspace: project worktree due to project binding (see Observed trace).
- No repository files, tests, production systems, network services, or external provider integrations may be accessed.
- Do not create `TODO_test-engineer.md`; this is a deliberate adaptation of the retrieved prompt to this project's read-only smoke-test boundary.
- Do not set `--model`, `--provider`, or `--reasoning`; inherit the active Hermes `default` profile.
- Gateway stays stopped; dispatch exactly this one card explicitly.

## Prompt template
- Source: prompts.chat **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl`, searched and retrieved on 2026-10-30: https://prompts.chat/prompts/cmmx34zl7000vil04rm2wl8yl_test-engineer-agent-role
- Modernized prompt: “Act as a read-only test verifier for HERMES-SMOKE-002. Confirm you received this card by returning the exact marker `CHPMIS_HERMES_SMOKE_002_RECEIVED`. Report only the task ID, assigned role, active profile/model/provider if exposed to you, workspace kind, and whether any files were changed. Do not inspect the project repository, run commands, create files (including the template's TODO file), or make product changes. Close the Kanban card with `kanban_complete(result=...)` if you can report the marker and trace; otherwise use `kanban_block(reason=...)`. Do not claim GUI visibility unless directly observed.”

## Acceptance criteria
- [ ] Exactly one Hermes Kanban card is created and explicitly dispatched.
- [ ] Card reaches a terminal result and reports the exact marker.
- [ ] Trace records card/run/session IDs, status, exit code, and observed profile/model/provider/workspace; unavailable fields are `NOT_EXPOSED`.
- [ ] No project files or product code are changed.
- [ ] Routing and ledger record only observed runtime details.

## Verification and report
- Command: Hermes role-task script with `--role worker --workspace scratch --project chanh-hung-pmis --wait 300 --max-runtime 180` and no model/provider/reasoning override.
- Record exact command outcome and returned card/session/run metadata. Do not infer GUI visibility from a session ID.

## Definition of Done
- [x] Prompt delivery and terminal result are evidenced.
- [x] Trace distinguishes observed fields from unavailable data.
- [x] `.team/ledger.md` includes this smoke run; `.team/routing.json` records verified routing and the workspace deviation.

## Observed trace
- Exact script exit code: 0. Card status `done`; result marker: `CHPMIS_HERMES_SMOKE_002_RECEIVED`.
- Card: `t_075840fe`; run ID: `24`; worker session ID: `20261030_154027_6bef15`; top-level `session_id`: `null` / `NOT_EXPOSED`.
- Profile: `default`; model: `gemini-3.8-flash-high`; provider: `custom` in Hermes run metadata (mapping not independently resolved); model/provider overrides were null.
- Workspace kind/path: `worktree`, `D:\\ANH VU\\Google Drive\\VUHOCAI\\Project\\CHANH HUNG PMIS\\.worktrees\\t_075840fe` (created despite requesting `scratch`). Hermes `git worktree list` did not register it; the generated directory was removed after inspection.
- Run metadata reported `files_changed: 0`; GUI visibility: `NOT_OBSERVED`. The existing dirty/untracked baseline was preserved; only this smoke task pack, routing and ledger trace were edited by Codex.
