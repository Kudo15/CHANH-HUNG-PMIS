# Hermes Kanban Lifecycle

Verified against Hermes Agent v0.21.6 (install: `C:\Users\ANHVU\AppData\Local\hermes`, source: `hermes-agent/hermes_cli/kanban*.py`, `gateway/kanban_watchers*.py`).

## Board storage

| Item | Location |
| --- | --- |
| Board root | `HERMES_KANBAN_HOME`, else the default Hermes root — `C:\Users\ANHVU\AppData\Local\hermes` |
| `default` board DB | `<root>\kanban.db` |
| Named board DB | `<root>\kanban\boards\<slug>\kanban.db` |
| Scratch workspaces | `<board root>\workspaces\<task id>\` |
| Worker logs | `<board root>` worker-logs dir, one `<task id>.log` per card (append, rotated) |
| Attachments | `<board root>\attachments\<task id>\` |

The board root is **shared across profiles by design** (`kanban_home()` in `kanban_db.py`), so a card created from any profile or harness lands on the board the desktop GUI reads. `HERMES_KANBAN_DB` pins a specific DB; the dispatcher injects it into every worker.

Inspect with `hermes kanban boards show` (slug, display name, DB path, task count) and `hermes kanban boards list`.

## Statuses

`triage` -> `todo` -> `ready` -> `running` -> `review` -> `done`, with `blocked`, `scheduled`, `archived` off to the side. These are the exact values accepted by `hermes kanban list --status`.

| Status | Meaning |
| --- | --- |
| `triage` | needs a spec; `hermes kanban specify <id>` fleshes it out and promotes to `todo` |
| `todo` | open parents/dependencies still running |
| `ready` | dispatchable — waiting for a dispatcher tick |
| `running` | a worker holds the claim (`HERMES_KANBAN_RUN_ID`) |
| `review` | implementation done, awaiting a reviewer verdict — **not** a block |
| `blocked` | worker or circuit breaker parked it; `hermes kanban unblock <id>` returns it |
| `scheduled` | parked on time, not on human input |
| `done` | closed with a result |
| `archived` | soft-hidden |

`hermes kanban decompose <id>` splits a triage card into children; `hermes kanban promote <id> "reason"` pushes a card forward.

## Dispatcher

- Embedded in the **gateway**: `GatewayKanbanWatchersMixin._kanban_dispatcher_watcher`, gated by `kanban.dispatch_in_gateway` (default true), one tick per `kanban.dispatch_interval_seconds` (default 60, floor 1).
- When the gateway is not running, an **external `hermes kanban daemon`** is expected. `hermes kanban dispatch` runs one tick on demand.
- One writer at a time: a non-blocking tick lock per board DB. A losing dispatcher writes nothing and returns an empty result (`skipped_locked`).
- Worker spawn argv: `hermes -p <profile> --cli --accept-hooks [--skills X]... [-m model] [--provider P] [--reasoning L] [--toolsets ...] chat -q "work kanban task <id>"`. `--cli` is mandatory — a worker that boots the TUI exits 0 without doing the work.
- Spawn env: `HERMES_KANBAN_TASK`, `HERMES_KANBAN_DB`, `HERMES_KANBAN_RUN_ID`, plus the claim lock. Windows uses `start_new_session=True` and `CREATE_NO_WINDOW`, so workers outlive the dispatching shell.
- Failure accounting: `spawn_failed`, `timed_out`, `crashed` count toward a circuit breaker that auto-blocks a card after `--failure-limit` consecutive failures (CLI default 2). Orphaned `running` cards whose PID is gone go back to `ready`.
- `--max-runtime` on the card becomes `max_runtime_seconds`; exceeding it emits `timed_out`.
- `hermes pause` is an emergency stop for cron **and** kanban dispatch; `hermes resume` lifts it.

Relevant `kanban.*` config keys (in `config.yaml`): `dispatch_in_gateway`, `dispatch_interval_seconds`, `max_spawn`, `max_in_progress_per_profile`, `default_assignee`. Changes need a gateway restart.

## Card JSON (`--json`)

`hermes kanban create/show --json` task fields:

`id, title, body, assignee, status, priority, tenant, workspace_kind, workspace_path, branch_name, project_id, created_by, created_at, started_at, completed_at, result, skills, max_runtime_seconds, max_retries, model_override, provider_override, session_id, workflow_template_id, current_step_key, completion_contract, last_failure_error`

`session_id` links the card to the Hermes session the worker ran — that is the session the GUI opens from the card.

Run records (`hermes kanban show <id> --json`, `hermes kanban runs <id> --json`):

`id, profile, step_key, status, outcome, summary, error, metadata, worker_pid, started_at, ended_at`

## Worker-side tools

A dispatched worker gets these `kanban_*` tools and is expected to close its own card:

`kanban_show, kanban_list, kanban_comment, kanban_complete, kanban_request_review, kanban_request_changes, kanban_block, kanban_schedule, kanban_heartbeat, kanban_attach, kanban_attach_url, kanban_attachments, kanban_edit, kanban_create, kanban_link, kanban_specify`

`kanban_complete` and `kanban_request_review` accept a structured handoff summary and metadata (for example `{"changed_files": [...], "tests_run": 12}`), which downstream cards and reviewers read. A worker that exits without calling one of them leaves the card `running`; the dispatcher logs a protocol violation and re-queues it.

## Workspaces

`--workspace` accepts `scratch`, `worktree`, `worktree:<path>`, `dir:<path>`.

Resolution (`_resolve_worktree_workspace`):

1. No path given -> the board's `default_workdir` must be set and absolute and inside a git repo; otherwise dispatch raises `ValueError` and the card never starts.
2. Path given -> must be absolute. If it is a git repo root (or inside one), the worktree is created at `<repo>\.worktrees\<task id>` on `branch_name` (default `wt/<task id>`).
3. A path that is already another task's linked worktree is not reused — the dispatcher falls back to its own `<repo>\.worktrees\<task id>` to avoid two cards sharing a branch.

Cleanup after completion removes `scratch` dirs and linked worktrees, deferred while another live task still uses the path, and skipped when the worktree is dirty or has unpushed commits. `.worktrees` is git-ignored automatically.

## Swarm

`hermes kanban swarm "<goal>" --worker PROFILE:TITLE[:SKILL,SKILL] --verifier PROFILE --synthesizer PROFILE` builds a root card plus parallel worker cards, a verifier gate, and a synthesizer card, wired with parent/child dependencies. Workers run in parallel only while `kanban.max_in_progress_per_profile` allows it.

## GUI

The desktop app renders the board (Kanban / Board view: cards, columns, board settings) from the same machine-level DB, and opens a card's worker session from the card. The backend it connects to is `hermes serve` (`backend-ownership.json` in `%APPDATA%\Hermes` records the owning PID and profile). CLI and GUI therefore share state without any sync step; the GUI does not need to be running when the card is created.
