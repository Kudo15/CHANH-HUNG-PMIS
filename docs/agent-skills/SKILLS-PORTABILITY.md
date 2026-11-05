# Skill inventory and PC transfer notes

This inventory records skills and role workflows explicitly referenced as used in `.team/ledger.md`, task packs, and project handoffs. It distinguishes copied instruction files from tools/services that must be installed and signed into separately.

## Project copies

| Skill | Project copy | Recorded use |
|---|---|---|
| `prompt-lookup` | `.agents/skills/prompt-lookup/` (already present; read-only in this session) | Search and retrieve real prompts.chat templates cited by Worker/Tester/Reviewer packs. |
| `superpowers:brainstorming` | `docs/agent-skills/brainstorming/` | Frame alternatives and owner decisions before approved design work. |
| `superpowers:receiving-code-review` | `docs/agent-skills/receiving-code-review/` | Independently assess review feedback against source, requirements, and scope. |
| `superpowers:requesting-code-review` | `docs/agent-skills/requesting-code-review/` | Prepare separate review requests and evidence. |
| `superpowers:subagent-driven-development` | `docs/agent-skills/subagent-driven-development/` | Plan bounded role runs and review gates. |
| `superpowers:systematic-debugging` | `docs/agent-skills/systematic-debugging/` | Trace defects and test/environment failures to causes. |
| `superpowers:test-driven-development` | `docs/agent-skills/test-driven-development/` | Require observed RED then GREEN for implementation tasks. |
| `superpowers:using-superpowers` | `docs/agent-skills/using-superpowers/` | Select and apply relevant process skills. |
| `superpowers:verification-before-completion` | `docs/agent-skills/verification-before-completion/` | Check fresh evidence and scope before reporting completion. |
| `superpowers:writing-plans` | `docs/agent-skills/writing-plans/` | Bound implementation plans, verification, and handoffs. |
| `opencode-role-agents` | `docs/agent-skills/opencode-role-agents/` (source); `.agents/skills/opencode-role-agents/` (Codex-discoverable PC copy) | Run/trace independent OpenCode Worker, Tester, and Reviewer sessions. Keep the two copies synchronized. |
| `hermes-role-agents` | `docs/agent-skills/hermes-role-agents/` | Prepare/dispatch/trace Hermes role cards. |
| `trace` | `docs/agent-skills/trace/` | Summarize delegated runs, metrics, evidence, and limits. |

The copied Superpowers content is from the installed `openai-curated-remote/superpowers` package version `7.0.1`; its license is included at `docs/agent-skills/superpowers-LICENSE.txt`. The other copies preserve their installed skill resources. `prompt-lookup` was already vendored by the project and was not overwritten.

## Prompt templates referenced by task packs

These are prompt-library records, not installed skills. Re-run prompt lookup on a new machine if access to prompts.chat is needed; task packs preserve the IDs and adaptations already used.

- prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa` — recurring Worker template.
- **Test Engineer Agent Role**, ID `cmmx34zl7000vil04rm2wl8yl` — Tester template.
- **Senior Code Reviewer (severity-ranked)**, ID `cmv9n79m30005ku060pzornri` — Reviewer template.
- **System Architect Agent Role**, ID `cmmx2hvgz0001ks04mcg6dizn` — architecture/planning template.
- **Vulnerability Auditor Agent Role**, ID `cmmx31zon000dk604l79f55ac` — security review template.

See the individual `.team/tasks/*.md` packs for exact adaptations, scope, and evidence. A template is not policy approval and does not expand a task's file allowlist.

## Continue on another PC

1. Clone the GitHub repository after an authorized checkpoint is published. The current checkout has uncommitted changes; a fresh clone will not contain them until they are deliberately reviewed and committed.
2. Read `AGENTS.md`, `.team/CHARTER.md`, `TASKS.md`, `PLAN.md`, `OPEN_QUESTIONS.md`, and the current task pack before continuing. Check `git status` and preserve any work already present.
3. Skill copies under `docs/agent-skills/` keep instructions with the repository. The project prompt-lookup skill remains under `.agents/skills/`. Codex may require relevant skill directories to be installed/recognized in its skill search path on the new PC; use the project-local conventions and verify discovery in that Codex version.
4. Install external tools separately as needed (Codex, Node/Python/Docker, Hermes/OpenCode CLIs). Skill files do not include those applications, accounts, service state, model/provider access, CLI permissions, or machine-local boards/sessions. Do not copy API keys, `.env`, credentials, or local database volumes through Git.
5. Set up a new synthetic local environment from `.env.example`; use loopback-only bindings and a disposable database. Follow `README.md` for versions and commands, and the task-specific verification commands for the active task.
6. Do not assume runtime services, Docker volumes, Windows Registry state, credentials, or agent sessions transfer with a clone. Recreate only within the current task's approved scope and Human Gates.

## Current transfer blockers / proposed next actions

- This checkout reported no configured Git remote. The project charter says not to create a remote or push, so remote publication was not performed. Owner/maintainer needs to resolve that project-level gate through the project's approved process.
- Before making a checkpoint, review the existing dirty/untracked files individually. Do not stage them wholesale: the starting checkout contained active task, product, test, CI, and isolated configuration changes. Decide which belong in the checkpoint, run their assigned independent review/verification gates, then commit/publish only through an authorized workflow.
- After an authorized checkpoint exists, verify the GitHub clone on PC 2, install/sign into required tools there, and resume the active task from its pack. Current project status and remaining gates are recorded in `TASKS.md`, `ACCEPTANCE.md`, and `.team/ledger.md`.
