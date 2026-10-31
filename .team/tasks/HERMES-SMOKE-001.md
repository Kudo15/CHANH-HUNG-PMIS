# Task Pack — HERMES-SMOKE-001

## Role and purpose
- Task ID: HERMES-SMOKE-001
- Role: Hermes Worker smoke test, dispatched manually by the coordinator
- Purpose: Verify one Hermes `delegate_task` call and whether its session is visible in Hermes Desktop.

## Scope and safety
- The child must return exactly `PING` and do nothing else.
- No repository, project data, source files, network, shell, or provider configuration may be read or changed by the child.
- Use the configured Hermes default profile and inherited model/fallbacks. Do not override provider or model.
- This is a dispatch smoke test, not product work. No PASS is assigned until dispatch and GUI visibility are evidenced.

## Prompt template
- Search result: `Test Engineer Agent Role`, prompts.chat ID `cmmx34zl7000vil04rm2wl8yl`.
- Modernized for this bounded smoke test: dispatch one isolated worker; verify the exact returned text and session evidence; ignore generic coverage/mutation targets and all code-writing instructions in the template.

## Definition of Done
- Parent Hermes session makes exactly one `delegate_task` call.
- One child result equals exactly `PING`.
- Capture the Hermes parent session ID and child/task ID if emitted.
- Verify whether the parent/child appears in Hermes Desktop; otherwise record GUI visibility as `NOT_VERIFIED`.

## Execution evidence
- Result: CLI dispatch succeeded; exactly one `delegate_task` call returned child summary `PING`.
- Command exit: `hermes_chat_exit=0`.
- Parent session: `20261029_212049_26ebfa`.
- Child delegation: `deleg_78599acd` (task index 0).
- Model observed from Hermes stream: `gemini-3.8-flash-high`; provider/profile were not exposed by the output.
- GUI check: `NOT_VERIFIED`. Computer Use found the Hermes Desktop window, but screenshot capture timed out twice (`FrameArrived timed out`, then `window capture timed out`). A successful CLI `--oneshot` dispatch alone does not prove that the task is visible in Desktop.
- Verdict: PARTIAL. Dispatch path works; GUI visibility criterion remains open for a visual check in Hermes Desktop.

## Follow-up GUI retry — 2026-10-29
- Reset the Computer Use session and re-enumerated the Hermes Desktop app. It is running and exposes one window titled `Hermes`.
- Screenshot capture failed on the fresh attempt with `FrameArrived timed out`, and failed again after refreshing the window list and activating that window with `window capture timed out`.
- No GUI session was created or claimed in this retry. The Desktop UI worker path remains `NOT_VERIFIED`; existing CLI `PING` evidence remains separate.

## Hermes setup discovery — 2026-10-29
- `hermes profile list`: active profile `default`, model `gemini-3.8-flash-high`.
- `hermes status --full` (exit 0): provider `easycliproxyapi`; scheduled jobs `0`; gateway `stopped`. API key values were not recorded.
- `hermes project create "CHANH HUNG PMIS" --slug chanh-hung-pmis --primary "D:\\ANH VU\\Google Drive\\VUHOCAI\\Project\\CHANH HUNG PMIS" --description "Project-scoped Hermes sessions for CHÁNH HƯNG PMIS; worker tasks require isolated worktrees and task packs." --use` (exit 0): created and activated project `chanh-hung-pmis`, ID `p_4aea8282`, primary repository root as requested.
- `hermes --help` confirms the CLI has `--worktree`; this does not prove the GUI will create/use an isolated worktree.
- Dry-run outcome: `BLOCKED` at GUI session creation/verification because the Hermes window could not be captured. No worker/reviewer GUI sessions, product edits, bots, or schedules were created.
- Reused prompt-librarian evidence: `Test Engineer Agent Role`, prompts.chat ID `cmmx34zl7000vil04rm2wl8yl`; prompt text was retrieved and adapted earlier. GUI session did not run, so no worker prompt was dispatched.

## GUI smoke retry — 2026-10-29
- `sky.list_apps()` returned Hermes Desktop window `Hermes`.
- Accessibility snapshot (without screenshot) succeeded. It showed `SESSIONS` and `BOTS`, the CHANH HUNG PMIS project group, and `Backend ready`; the project had no sessions. The active open conversation still belongs to `openbullet`.
- Screenshot capture still times out. Accessibility click attempts fail with `coordinate input geometry is unavailable`, so I did not submit a prompt or create a session in the wrong project.
- Result: Desktop UI and backend status are visible/readable. Worker GUI session creation and result are `BLOCKED` / `NOT_VERIFIED`; no GUI `PING` test was completed.

## Cross-surface check — 2026-10-29
- `hermes project list` (exit 0) marks `chanh-hung-pmis` as the active CLI project.
- `hermes sessions list --workspace "CHANH HUNG PMIS" --limit 5` (exit 0) returns the earlier CLI session `20261029_212049_26ebfa` (`Task ID HERMES-SMOKE-001.`).
- The Desktop accessibility tree still does not show that session under the CHANH HUNG PMIS project; the selected conversation/footer is `openbullet`.
- The in-app New session button is visible, but click input fails with `coordinate input geometry is unavailable`; `Ctrl+N` left the UI state unchanged. No second task was sent.
- Conclusion: the Hermes backend and session store work; Desktop UI renders and reports `Backend ready`, but task/session launch into the visible CHPMIS project is still `BLOCKED` / `NOT_VERIFIED`.
