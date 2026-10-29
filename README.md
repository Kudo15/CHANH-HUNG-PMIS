# CHÁNH HƯNG PMIS

Secure modular-monolith project information management system for Ban QLDA phường Chánh Hưng.

## Current stage

Planning and product/security proposals are documented. Repository audit found no application code, dependencies, migrations, or project test commands. Product implementation has not started.

## Start here

1. Read `AGENTS.md` and `.team/CHARTER.md`.
2. Review `docs/MISSION.md`, `docs/product/PRD.md`, and `OPEN_QUESTIONS.md`.
3. Review the first vertical slice plan at `docs/superpowers/plans/2026-10-29-chanh-hung-pmis-vertical-slice.md`.
4. Resolve Human Gates and install/verify prompt-lookup before dispatching Worker tasks.

## Project documents

- Mission and PRD: `docs/MISSION.md`, `docs/product/PRD.md`
- Roles and stories: `docs/product/USER_ROLES.md`, `docs/product/USER_STORIES.md`
- Architecture/API/data: `docs/architecture/`
- Workflow and security: `docs/workflows/`, `docs/security/`
- Legal register: `docs/legal/LEGAL_RULES_REGISTER.md`
- Acceptance/tasks/open questions: `ACCEPTANCE.md`, `TASKS.md`, `OPEN_QUESTIONS.md`

## Tooling status

- Superpowers exists in the current Codex skill catalog.
- Prompt-search skill `prompt-lookup` is installed in `.agents/skills/prompt-lookup`; Codex is connected to `https://prompts.chat/api/mcp`. Search and retrieval were verified for architecture, code review, and testing templates; adapted template IDs and links are recorded in the Worker task pack.
- Node 22.23.2/npm 10.9.8 and Python 3.12/3.13 are available. Docker is not installed, so Compose runtime/config checks cannot currently be executed.
- Hermes `--version` failed with exit code 1 because this user cannot write the install-state lock. No permissions or providers were changed; profiles/models/Kanban/GUI remain unverified.
- Git was initialized locally; no remote, commit, push, or deployment was created.
