# OpenCode role agents — troubleshooting

| Symptom | Check | Fix |
| --- | --- | --- |
| `Model unavailable: provider/model` | `opencode models`, provider endpoint | Pick a listed model with `--model`, or fix the provider in `~/.config/opencode/opencode.jsonc` |
| `unknown provider for model ...` from a custom provider | The local proxy behind the provider's `baseURL` may not serve that model id | Use a model id the proxy lists, or switch provider |
| `opencode` is not recognized (PowerShell/cmd) | Check `PATH`; use the driver, which locates native binaries | Run `node scripts/opencode-role-task.mjs --status`; if needed set `OPENCODE_CLI_BIN` to a native executable |
| `spawnSync ...\npm\opencode ENOENT` | Node selected npm's extensionless shim, not its native executable | Use `%APPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`; the current driver resolves that npm package path automatically |
| `--status` says `version: -`, `desktop app: not running`, `api: -` and exits 1/6 | Are you inside a sandbox (Codex, CI)? The checks spawn the bundled exe, read the log and state file, call `tasklist` and connect to 127.0.0.1 | Rerun elevated / outside the sandbox; `desktop app: unknown` means the process listing itself was blocked. These checks cost nothing |
| `PlatformError: PermissionDenied: FileSystem.open (...opencode\\log\\opencode.log)` | Sandbox blocked the CLI's log file | Same as above: grant access or rerun elevated; do not work around it by moving the log |
| Run finished but no session in the GUI | Was `--standalone` passed? Does `--status` show the same URL the desktop uses? | Never use `--standalone`; let the driver start the service; reopen the project in the GUI |
| `gui_visible: false` in the record | `opencode session list` in the same `cwd` | The session may belong to another project dir; rerun in the right directory or refresh the GUI |
| Session lands in the caller's directory instead of `--repo`/`--cwd` | `session export <id>` shows `info.location.directory` | The CLI resolves the project from `PWD`; the driver sets it from the target dir, so do not spawn it yourself without doing the same |
| Reviewer or verifier wrote files | Agent bash permissions | `edit: deny` only covers the edit tool; keep bash a `"*": deny` map with an allowlist; never widen it to `bash: allow` |
| Reviewer/verifier denied on `cat x && git status` or `git diff \| head` | Command chains are matched whole, not part by part | Expected: run one simple command per tool call; the role prompts say so |
| `agent not found` / role prompt ignored | Check the role-agent filenames and the CLI/config location; do not inspect credentials | If the agent file is unmarked or newer, it is preserved and dispatch blocks. Review the file first; use `--force-agents` only when replacing it is intended |
| CLI not found, exit 6 | `OPENCODE_CLI_BIN`, `PATH` | Point `OPENCODE_CLI_BIN` at `opencode-cli.exe`, not at a `.cmd` shim |
| Windows `.cmd` cannot be spawned | The driver refuses shell shims | Use the `.exe` from the desktop bundle or a native install |
| Body too long, exit 2 | Body > 30000 chars | Split the task or trim the body file; the Windows command line caps near 32767 |
| Invalid `--timeout`, exit 2 | Value is non-numeric, non-finite, zero, or negative | Pass a finite positive number of seconds; values under 30 seconds are clamped to 30 |
| Timeout, exit 5 | Session in GUI may still be busy | Open the session in the GUI, check for a running tool, or rerun with a larger `--timeout` |
| Reviewer wrote files | Agent permissions | Use `role-reviewer` / `role-verifier`; keep the `"*": deny` bash map; never bypass a `deny` |
| `opencode service restart` broke the GUI | Restart drops GUI clients | Only restart on user request; reopen the desktop app afterwards |
| `Background service failed to start` on every command | `~/.local/state/opencode/service.json` (pid/url) and the service log `~/.local/share/opencode/log/opencode.log` | A stale service can stay bound to the port in a half-booted state (`background service boot failed`, e.g. `SQLiteError: disk I/O error` while `/api/info` returns 500). The driver stops at preflight with exit 6 and names the pid to kill; kill it, then rerun and the driver starts a fresh service |
| Service boot failed with a SQLite error | Copy `opencode.db*` elsewhere and run `PRAGMA integrity_check` on the copy | If the copy is `ok`, the files are fine and only the process was wedged: restart the service. Do not delete the WAL or the db |
| Multiple projects, sessions in the wrong place | Session is keyed by `cwd` | Run worker and reviewer in the same directory, or accept separate GUI projects |

## GUI visibility checklist

1. The run must use the background service: no `--standalone`, no private `--server` URL.
2. `node scripts/opencode-role-task.mjs --status` must exit 0 with `api: ok` and the shared service URL. The driver resolves a native CLI executable, including the npm package binary on Windows.
3. The session is listed by `opencode session list` in the same project directory.
4. The GUI shows the project; if the folder is not open, open it in the desktop app.
5. Look under **Home -> Today** for the session. The rail below `New session` only lists open
   tabs, so a session that was never opened in the app is missing there by design.

Do not claim GUI visibility from anything other than the `gui_visible` flag or a user confirmation.
