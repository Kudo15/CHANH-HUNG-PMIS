# Troubleshooting

Diagnose before changing anything. Read-only commands first: `hermes kanban show <id> --json`, `hermes kanban diag`, `hermes kanban runs <id> --json`, `hermes kanban log <id> --tail 8000`, `hermes gateway status`, `hermes status`.

## Card stays in `ready`, nothing runs

1. `hermes gateway status` — if the gateway is stopped there is no embedded dispatcher.
2. Start one: `hermes kanban daemon --interval 15 --pidfile "$TEMP/hermes-kanban.pid" &`, or dispatch on demand: `hermes kanban dispatch --max 1 --json`.
3. `hermes kanban diag` — check for an emergency stop; `hermes pause` halts kanban dispatch until `hermes resume`.
4. `--dry-run` shows what a tick would spawn without touching state: `hermes kanban dispatch --dry-run`.
5. Unassigned cards are skipped. Confirm `assignee` in `hermes kanban show <id> --json`.

## Card auto-blocked after a couple of attempts

The circuit breaker blocks a card after `--failure-limit` consecutive `spawn_failed` / `timed_out` / `crashed` results (default 2).

1. `hermes kanban log <id> --tail 8000` for the worker's own output.
2. `hermes kanban show <id> --json` -> `last_failure_error`.
3. `hermes doctor` for provider auth and dependency problems; `hermes status` for the active model/provider.
4. After fixing the cause: `hermes kanban unblock <id> --reason "provider auth fixed"`.

## Worktree errors at dispatch

| Message | Cause | Fix |
| --- | --- | --- |
| `workspace_kind=worktree but no workspace_path, and board ... has no default_workdir` | bare `--workspace worktree` | pass `--workspace worktree:<absolute repo path>`, or set it once: `hermes kanban boards set-default-workdir <absolute repo path>` |
| `default_workdir ... is not absolute` | relative board workdir | use an absolute path |
| `... is not inside a git repo` | path is not a repo | point `--repo` at the repo root |
| `non-absolute worktree path` | relative `worktree:` value | absolute path only |
| `git worktree add failed for <target> on branch <branch>` | branch exists, dirty tree, or locked index | pick another `--branch`, clean the repo, then `hermes kanban unblock <id>` |

Worktrees are created at `<repo>\.worktrees\<task id>`; `.worktrees` is git-ignored automatically.

## GUI shows nothing

1. `hermes kanban boards show` — note the DB path, then confirm the desktop app is on the same board: `hermes kanban boards list` (the `●` marks the active board). A card created while another board was active lives in that board's DB.
2. Check for env pins in the harness shell: `HERMES_KANBAN_DB`, `HERMES_KANBAN_HOME`, `HERMES_KANBAN_BOARD` redirect writes away from the board the GUI reads. Unset them for harness-driven cards.
3. Profiles share one board root by design, so `-p <profile>` does not fork the board. If a profile was installed with its own `HERMES_HOME`, verify the DB path again.
4. The GUI does not have to be running at create time; open it afterwards and the card is there.
5. Archived cards are hidden: `hermes kanban list --archived`.

## Card stuck in `running` with no worker

The worker PID is gone (crash, reboot, killed shell):

1. `hermes kanban runs <id> --json` — look at `worker_pid`, `status`, `outcome`.
2. `hermes kanban reclaim <id> --reason "stale claim"` releases it; the dispatcher also requeues detected orphans to `ready`.
3. A worker that exits without calling a `kanban_*` verb logs a protocol violation and is re-queued automatically. Strengthen the role contract in the card body (`Finish with exactly one of: kanban_complete / kanban_request_review / kanban_block`) and re-dispatch.

## Review never gets picked up

`review` is a lane, not a block — it still needs a dispatcher tick.

1. `hermes kanban show <id> --json` — confirm `status: review` and the `assignee`.
2. Assign the reviewer explicitly: `hermes kanban request-review <id> --summary "..." --reviewer default`.
3. Reviewer verdicts: `hermes kanban request-changes <id> "reason"` returns the card to the implementer; `hermes kanban complete <id> --result "approved: ..."` closes it; `hermes kanban reopen-review <id> --reason "..."` reopens.
4. `request-review --force` overrides the live-claim guard on a running card — use only when the worker is provably gone.

## Parallel cards run one at a time

`kanban.max_in_progress_per_profile` caps concurrent runs per profile. With every card assigned to `default`, extra cards are deferred (reported as `skipped_per_profile_capped`, not as failures) and picked up on later ticks.

Options, in order of preference: keep the fan-out small, raise the cap in `config.yaml` (needs a gateway restart), or create dedicated role profiles (`hermes profile create worker --description "..."`) — ask the user before changing profiles or config.

## Timeouts

`--max-runtime` on the card caps the worker; exceeding it emits `timed_out` and counts toward the circuit breaker. Raise it for large tasks (`--max-runtime 3600`) rather than retrying blindly. `hermes kanban tail <id>` streams events while a run is in flight.

## Wrong model or provider on the worker

The card's `model_override` / `provider_override` are pinned into the worker argv, and the provider is pinned alongside the model to avoid resolving against the wrong backend. Set both (`--model`, `--provider`) or neither; `hermes kanban set-model <id> ...` changes an existing card and takes effect on the next dispatch.
