---
name: opencode-role-agents
description: Delegate a bounded task to the OpenCode CLI as a role agent (worker, reviewer, verifier) from another harness - create a ledger card, run it headlessly through the shared OpenCode background service so the session stays visible in the OpenCode Desktop GUI, wait for the outcome, and report back. Use when the user asks to run work through OpenCode, hand a task to an OpenCode worker or reviewer, fan out parallel OpenCode workers, or wants an OpenCode-side second opinion on a diff. Do not use for edits the harness should make itself, for one-line questions, or when the OpenCode CLI is not installed and signed in.
---

# OpenCode Role Agents

Run the OpenCode CLI as a delegated role agent from inside another harness. The role is a
markdown agent installed under `~/.config/opencode/agents/`, the task runs headlessly against the
OpenCode background service, and every run is recorded in a ledger so it stays inspectable.

## Why this skill exists

Qoder CLI runs never appear in the Qoder Desktop GUI. OpenCode runs do: `opencode run` talks to
the same background service the desktop app is connected to, so the session appears in the GUI's
session list while it runs and can be reopened there afterwards. The only thing that breaks this
is `--standalone`, which starts a private server and hides the run. **Never pass `--standalone`.**

## Overview

| Piece | What it is |
| --- | --- |
| Role | `~/.config/opencode/agents/role-<role>.md`, invoked with `run --agent role-<role>` |
| Run | One `opencode run --format json ... <body>` invocation against the shared service |
| Service | `service status` on the resolved CLI prints the URL; the desktop app is a client of it |
| Sessions | Stored by the service in `~/.local/share/opencode/opencode.db`, keyed by project dir |
| Ledger | `~/.opencode/role-runs/board.jsonl` plus `runs/<run_id>/` (prompt, stdout, stderr, meta) |
| Resume | `opencode run --session <id> "<body>"`, or open the session in the GUI |
| Cost | `opencode session export <id>` -> `info.cost`, `info.tokens`, `info.outcome` |

## When to use

Use it when the user asks for an OpenCode-side worker or reviewer, wants an independent second
implementation or review pass, or wants parallel OpenCode workers on separable subtasks.

Do not use it for a change you can make directly, for questions answerable by reading a file, or
when `opencode` is missing or no model is available.

## Preflight

Run these before the first delegation of a session. They are free; an actual run is billable.

```bash
node <skill>/scripts/opencode-role-task.mjs --status
```

`--status` resolves a native CLI executable, prints the version, the service URL, the state pid,
whether the desktop app is running and whether `/api/info` answers; exit `0` means the shared-service
preflight passed. A completed delegation is only confirmed GUI-visible when its run record says
`gui_visible: true`. Inside a sandbox (Codex, CI) these checks can be blocked: you will see
`version: -`, `desktop app: unknown` and an exit `6` that says so. Rerun with the needed access rather
than treating it as a broken service. For the model list use the resolved binary directly:

```bash
"%LOCALAPPDATA%\Programs\ai.opencode.desktop\resources\opencode-cli.exe" models
```

On Windows, PowerShell may resolve `opencode` to an npm `.ps1`/`.cmd` shim, which `spawnSync` cannot
run directly. The driver selects a native executable in this order: `OPENCODE_CLI_BIN`, `opencode.exe`
on `PATH`, the npm package binary at `%APPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`,
then the Desktop bundle at `%LOCALAPPDATA%\Programs\ai.opencode.desktop\resources\opencode-cli.exe`.
If discovery is ambiguous, set `OPENCODE_CLI_BIN` to the native `.exe`; never point it at a shell shim.
On macOS/Linux it resolves the native `opencode` executable from `PATH` (or the macOS Desktop bundle).
If the background service is not running the driver starts it once, because a private server would hide the run.

## Fast path

```bash
node <skill>/scripts/opencode-role-task.mjs \
  --title "Add --verbose flag to cli.mjs" \
  --role worker \
  --body-file /tmp/task.md \
  --repo /abs/path/to/repo \
  --model deepseek/deepseek-flash \
  --timeout 1800
```

Add `--dry-run` first to see the exact command and body without running anything. Always pass a
`--body-file` for multi-line requirements; `--body` is for one-liners.

Exit codes: `0` done, `3` review requested, `4` blocked, `5` timeout, `1` run failed,
`6` CLI unusable, `7` not signed in / no model available, `2` usage error.

## Manual path

Equivalent invocation when the script is unavailable (`<cli>` is the resolved binary, e.g. the
bundled `opencode-cli.exe`; `opencode` itself is usually not on `PATH`):

```bash
"$OPENCODE_CLI" run --agent role-worker --format json --auto \
  --title "worker: Add --verbose flag" \
  "<requirement text>

Finish with exactly:
SUMMARY: <one line>
ROLE_RESULT: done|review|blocked"
```

Pass the message as one positional argument. This build treats `--` as a positional too and
duplicates the prompt, so do not insert a `--` separator; the driver prepends `Task:` when the
body would start with a dash.

Then record the run yourself: append one JSON line to `~/.opencode/role-runs/board.jsonl` with
`run_id, ts, title, role, status, cwd, session_id, model_used, cost_usd, exit_code, summary`, and
keep stdout/stderr under `~/.opencode/role-runs/runs/<run_id>/`. Without that step the run is
only visible in the GUI, not in the ledger.

## Role contracts

The prompt text lives in the skill's `agents/role-<role>.md`. The driver installs missing files
into `~/.config/opencode/agents/` and upgrades only recognized older skill-marked copies. Unmarked or
newer files are preserved and block dispatch unless `--force-agents` is explicitly passed; edited
current-version files with the role-result contract are preserved by default. Every role must end its reply with the
two machine-readable lines; the driver greps them to decide the exit code. Keep them verbatim.

- **worker** — reads before editing, implements completely, runs the project's own fast checks,
  stays in scope, commits only when asked. Permissions: `edit: allow`, `bash: allow`.
- **reviewer** — reads `git status` / `git diff` and the requirement, judges correctness, edge
  cases, scope creep and security, cites `file:line`, changes nothing. `edit: deny` plus a bash
  allowlist (`git`, `ls`, `cat`, `rg`, `grep`, `find`, `diff`, ...); every other command is denied.
- **verifier** — re-runs build/typecheck/tests, quotes the exact failing output, fixes nothing.
  `edit: deny` plus the reviewer commands and the common build/test runners (`node`, `npm`, `npx`,
  `pnpm`, `yarn`, `python`, `pytest`, `go`, `cargo`, `dotnet`, `make`, `tsc`, ...).

`--auto` only auto-approves OpenCode's `ask` permissions. An agent's `deny` rules still apply, so
the reviewer and verifier stay read-only even with `--auto`; a `pwsh Set-Content` probe is refused
with `permission.rejected`. Never lower a `deny` to get past it.

The allowlists are enforced by command pattern, not by the filesystem: an allowed runner can still
write build output, and shell redirection inside an allowed command is not inspected. The pattern
sees the whole command string, so a chain or pipe (`cat x && git status`, `git diff | head`) is
denied even when every part is allowed — reviewer and verifier are instructed to run one command
per call. For a hard read-only guarantee, point the reviewer/verifier at a throwaway checkout.

## Workspace rules

- `--repo` must be an absolute path inside a git repository; the driver resolves it with
  `git rev-parse --show-toplevel` and runs there. Without `--repo`, `--cwd` is used.
- This skill does not create worktrees. For isolation, create one yourself and pass it as `--cwd`;
  the reviewer/verifier should then point at the worker's worktree, not the main checkout.
- A session belongs to the project directory. Running in a different directory creates a separate
  GUI project, so keep the whole worker -> reviewer -> verifier loop in one directory.
- `--resume <id>` continues an existing session; without it every run is a new session.

## Visibility contract

OpenCode CLI runs are visible in the OpenCode Desktop GUI because both use the same background
service. After every delegation report all of the following:

1. `run_id` and ledger path (`~/.opencode/role-runs/board.jsonl`, run dir under `runs/<run_id>/`)
2. role, status, and the role's own `SUMMARY` line
3. project directory, plus the service URL from the record
4. `session_id` and the exact resume command: `opencode run --session <id> "continue"`
5. GUI hint: OpenCode Desktop -> project `<cwd>` -> session `<title or id>`
6. cost signal: `cost_usd`, `tokens`, `model_used` from the record
7. for a worker: `git -C <cwd> status --porcelain` and `git diff --stat` when the folder is a Git
   repository; if it is not, say so instead of reporting an empty diff

The driver sets `gui_visible` by re-reading `opencode session list` in the same project. If it is
`false`, say the session exists but GUI listing was not confirmed; do not claim otherwise.

In the desktop app the session appears under **Home -> Today** for that project. The rail under
`New session` only lists sessions that are currently open as tabs, so a fresh run does not show up
there until someone opens it; do not read that rail as the session list.

Show the board on request with `node scripts/opencode-role-task.mjs --list`.

## Review loop

1. Worker run -> note the session id and project directory from the ledger.
2. Reviewer run in the same project, with the requirement plus the worker's summary in the body.
3. Exit `3` (review requested) means the reviewer wants changes: start a **new** worker run in the
   same project using the reviewer's findings as the body. Do not resume the old session unless the
   user asks.
4. Verifier run last, when the requirement names checks that must pass.
5. Stop after two review rounds and report back instead of looping.

## Parallel fan-out

Split the goal into subtasks that touch disjoint files, then launch one script invocation per
subtask in the background, each in its own project directory or worktree (passed as `--cwd`). Cap
it at two or three concurrent runs unless the user asks for more, and confirm before the first
fan-out: every run is a separate billable agent session. The roles do not merge; merge yourself.

## Reporting back

Report the ledger facts, not a narrative: status, summary, project, session id, what was verified,
and what is still open. When a run fails, quote the tail of `runs/<run_id>/stderr.log`, the
`error_events` from the record, and the exit code. Never present an unverified claim from a role's
output as fact — say what the role claimed and what you checked.

## Safety

- Never use `--standalone`; it hides the run from the GUI.
- Never try to bypass an agent `deny` rule or a permission denial. Fix the cause or report blocked.
- Pass a finite positive `--timeout` for every delegation (minimum effective duration: 30s). The
  driver validates it before creating ledger files; its default is 1800s for direct invocations.
- Ask before the first run of a session and before any fan-out — these are real billable runs.
- Keep `--repo`/`--cwd` inside the workspace the user pointed at.
- Do not read or print credentials, `~/.config/opencode/service.json`, or any API key.
- Do not delete ledger entries or sessions without an explicit request.

## Resources

- `references/cli-contract.md` — verified flags, agent config, output shapes, storage, ledger schema
- `references/troubleshooting.md` — symptom -> check -> fix, including GUI visibility failures
- `scripts/opencode-role-task.mjs` — create/run/record/report driver (Node >= 18, stdlib only)
- `agents/role-*.md` — the role prompts installed into the OpenCode config
