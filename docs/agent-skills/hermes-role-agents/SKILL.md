---
name: hermes-role-agents
description: Delegate a bounded task to a Hermes Agent role (worker, reviewer, verifier) by driving the local `hermes` CLI - create a kanban card, dispatch it to the role, wait for the outcome, and report back. Use when the user asks to run work through Hermes, hand a task to a Hermes worker or reviewer, fan out parallel Hermes agents in isolated git worktrees, or delegate to Hermes while keeping the task visible in the Hermes desktop GUI. Do not use for edits the harness should make itself, for one-line questions, or when the `hermes` CLI is not installed.
---

# Hermes Role Agents

## Overview

Hermes Agent runs delegated work as **kanban cards**. A card carries the role prompt, the workspace, and model overrides. The dispatcher spawns `hermes -p <profile> --cli chat -q "work kanban task <id>"` inside that workspace, and the worker closes its own card with its `kanban_*` tools. All cards live in one machine-level SQLite board — the same board the Hermes desktop GUI renders — so a card created from any harness is visible in the GUI.

Role model on this machine: **role = prompt in the card body**, assignee = the `default` profile (the only profile that exists). Do not create Hermes profiles unless the user asks.

## When to use

Use for implementation work in an isolated worktree, review of a branch, parallel fan-out, or anything the user wants tracked on the Hermes board.

Do not use for a one-line answer, a file read, or work the harness should do itself in its own workspace.

## Preflight (read-only, run first)

```bash
hermes --version            # CLI present?
hermes kanban boards show   # prints the active board and its DB path
hermes gateway status       # is the embedded dispatcher running?
```

Board DB here: `C:\Users\ANHVU\AppData\Local\hermes\kanban.db`. The desktop GUI reads that same file, so cards created from a harness appear in its Kanban/Board view.

If the gateway is stopped there is **no dispatcher**. Either start one for the session:

```bash
hermes kanban daemon --interval 15 --pidfile "$TEMP/hermes-kanban.pid" &
```

or dispatch explicitly after each create (the default in the script below). Tell the user which you did — a card with no dispatcher sits in `ready` forever.

## Fast path: one command

```bash
node scripts/hermes-role-task.mjs \
  --role worker \
  --title "Add retry with backoff to the ingest worker" \
  --body-file /abs/path/spec.md \
  --repo /abs/path/to/repo \
  --created-by codex \
  --wait 900
```

Review pass over the result:

```bash
node scripts/hermes-role-task.mjs \
  --role reviewer \
  --title "Review: ingest retry backoff" \
  --body "Card t<id>, branch wt/t<id>. Verify correctness, tests, scope." \
  --repo /abs/path/to/repo \
  --created-by codex --wait 600
```

Useful flags: `--dry-run` (print the create command, change nothing), `--wait 0` (create + dispatch, return the card id), `--json` (machine-readable result), `--model`, `--provider`, `--reasoning`, `--skill` (repeatable), `--max-runtime`, `--branch`, `--workspace`, `--idempotency-key` (safe re-runs).

Exit codes: `0` done · `3` awaiting review · `4` blocked/failed · `5` timed out waiting · `2` usage or preflight error.

Requires Node >= 18 on PATH. If the harness has no Node, use the manual path.

## Manual path

Always pass the body with `--body-file`; bodies contain newlines and flag-like lines that break shell quoting.

```bash
# 1. card body = role contract + requirement
cat > /tmp/card.md <<'EOF'
ROLE: worker (implementation)
...role contract...
--- REQUIREMENT ---
...what to build, acceptance checks...
EOF

# 2. create (prints JSON with the card id)
hermes kanban create "Add retry with backoff" \
  --body-file /tmp/card.md \
  --assignee default \
  --workspace "worktree:C:\abs\path\to\repo" \
  --branch wt/ingest-retry \
  --created-by codex \
  --max-runtime 1800 \
  --json

# 3. dispatch (or rely on the gateway/daemon)
hermes kanban dispatch --max 1 --json

# 4. watch
hermes kanban show <id> --json      # status, result, session_id, branch
hermes kanban tail <id>             # live event stream
hermes kanban log <id> --tail 4000  # worker output

# 5. close it out if the worker did not
hermes kanban complete <id> --result "what changed, how verified"
```

## Role prompts

Put the contract at the top of the card body, then the requirement under `--- REQUIREMENT ---`. The closing contract is mandatory: a worker that exits without calling a `kanban_*` verb leaves the card `running` and gets re-dispatched.

**worker**

```
ROLE: worker (implementation)
Work only inside this task's workspace.
1. Read the requirement, then inspect the code before editing.
2. Make the smallest change that satisfies it; run the repo's checks/tests when available.
3. Commit on this task's branch when the workspace is a git worktree.
4. Post progress with kanban_comment.
Finish with exactly one of:
- kanban_complete(result=what changed, how it was verified, what is left)
- kanban_request_review(summary=...) when a human or reviewer must judge it
- kanban_block(reason=...) when you cannot proceed
```

**reviewer**

```
ROLE: reviewer
Judge the implementation; do not rewrite the feature.
1. Read the card body, the worker's summary and comments, and the diff on the task branch.
2. Check correctness, test coverage, and scope creep.
Finish with exactly one of:
- kanban_complete(result=acceptance verdict + evidence)
- kanban_request_changes(reason=concrete required changes)
- kanban_block(reason=...) when the review cannot be performed
```

**verifier** (swarm gate): same as reviewer, plus "run the acceptance commands yourself and paste the output into the result."

## Workspace rules

- `--workspace worktree:<absolute repo path>` — the path must be absolute. A bare `--workspace worktree` falls back to the board's `default_workdir`; this board has none, so dispatch fails loudly.
- The worktree lands at `<repo>\.worktrees\<task id>`, on `--branch` or `wt/<task id>`.
- `scratch` (default) is a throwaway dir under the board root — use it only when no repo is involved.
- `dir:<absolute path>` runs in an existing directory with no isolation. Avoid for parallel roles.
- `--project <slug>` anchors the worktree under a registered project (`hermes project list`).

## GUI visibility contract

The task must be visible in the Hermes desktop GUI. Guarantee it by:

- creating a real kanban card — never `hermes -z/--oneshot`, which produces a session but no card;
- using a recognizable title plus `--created-by <harness>` so the user can spot it on the board;
- reporting the card id, title, final status, workspace path, branch, and `session_id`;
- telling the user to open the Hermes desktop app -> Kanban/Board; the worker session opens from the card.

If the desktop app is closed, the card still exists and shows up when it is opened.

## Review loop

```bash
hermes kanban request-review <id> --summary "implemented X, tests Y" --reviewer default
hermes kanban request-changes <id> "concrete change needed"   # reviewer verdict: back to the implementer
hermes kanban promote <id> "reason"                           # push a card forward
hermes kanban reopen-review <id> --reason "new evidence"
```

## Parallel fan-out

```bash
hermes kanban swarm "Ship feature X" \
  --worker "default:Build API" --worker "default:Build UI" \
  --verifier default --synthesizer default --created-by codex --json
```

Swarm builds parallel worker cards -> verifier -> synthesizer. With a single profile, `kanban.max_in_progress_per_profile` can serialize them; cards then queue instead of running at once. Ask before raising it or creating profiles.

## Reporting back

Report the card id and title, final status, what changed, how it was verified, workspace path and branch, session id, and what is left. Summarize — do not paste the worker log; point at `hermes kanban log <id>`.

## Safety

- Never pass `--yolo`.
- Set `--max-runtime` (seconds) on every card.
- Dispatching spawns a real, billable agent run on the user's Hermes provider. Confirm before the first run of a session and before fanning out more than two cards.
- If nothing starts, check the emergency stop (`hermes pause` / `hermes resume`) and `hermes kanban diag`.
- Do not archive, delete, or reassign cards, boards, or profiles without an explicit request.

## Resources

- `scripts/hermes-role-task.mjs` — create -> dispatch -> wait -> report (Node >= 18, no dependencies).
- `references/kanban-lifecycle.md` — statuses, card/run JSON fields, worker tools, dispatcher behavior, config keys, DB paths.
- `references/troubleshooting.md` — card never dispatched, worktree errors, empty GUI, stuck claims, queued parallelism.
