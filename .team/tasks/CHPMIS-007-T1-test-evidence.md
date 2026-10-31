# CHPMIS-007-T1 — Independent Test Evidence

## Task identity and role

- **Task ID:** CHPMIS-007-T1
- **Role:** Tester / Verifier, read-only; Codex configured default (no model or effort override)
- **Prompt template:** `Test Engineer Agent Role`, prompts.chat ID `cmmx34zl7000vil04rm2wl8yl`, retrieved through `.agents/skills/prompt-lookup/` and adapted for read-only project verification. Source: https://prompts.chat/prompts/cmmx34zl7000vil04rm2wl8yl_test-engineer-agent-role
- **Workspace:** Existing project checkout after CHPMIS-007 Worker has finished. Run before the Hermes Reviewer.

## Objective and scope

Independently verify CHPMIS-007 frontend behavior and repository-defined checks against `.team/tasks/CHPMIS-007-project-workbench.md`, the design spec, and approved policy. Do not edit implementation, tests, docs, acceptance status, or ledger. Do not create a TODO file; report evidence in the task handoff.

## Definition of Done

- Inspect changed-file scope and map each applicable acceptance criterion to test or code evidence.
- Identify the exact repository-defined verification scripts before running them.
- Run `npm --prefix frontend run test -- --run`, `npm --prefix frontend run lint`, and `npm --prefix frontend run build`; run `npm --prefix frontend run test:e2e` only if the repository setup supports local execution without external services.
- Report every exact command, result, exit code, counts where applicable, and missing evidence as `NOT_VERIFIED`.
- Report scope violations and defects as findings; do not silently repair them.

## Trace and constraints

Frontend-local synthetic verification only. No real IdP, production, external services, Docker, or database claims. Preserve the working tree and leave all edits to a separately authorized Worker follow-up.

### Modernized Tester prompt

Using the retrieved Test Engineer Agent Role template, independently verify CHPMIS-007 against its task pack, approved policy and exact existing API contracts. First capture and inspect the post-Worker status/diff; keep the work read-only. Map every acceptance item to evidence. Discover the repository-defined commands, then run the required frontend test, lint and build commands exactly as listed. Run E2E only if the existing setup works locally without external services. Record exact command, salient output/counts and exit code; mark unrun runtime/browser/IdP evidence NOT_VERIFIED. Do not edit implementation, tests, docs, acceptance or ledger; report defects and scope violations as follow-up findings rather than fixing them. Do not create an extra TODO file or claim PASS without command evidence.

## Observed independent evidence — 2026-10-30

- `npm --prefix frontend run test -- --run` in the default sandbox: startup failed before tests, exit 1, due to `spawn EPERM` while Vite loaded Tailwind/Rolldown native modules. This is recorded as an environment limitation, not a product test failure.
- `npm --prefix frontend run test -- --run` with approved unsandboxed execution: **2 test files passed, 15 tests passed**, exit 0.
- `npm --prefix frontend run lint` with approved unsandboxed execution: exit 0, no diagnostics.
- `npm --prefix frontend run build` with approved unsandboxed execution: exit 0; TypeScript and Vite production build succeeded.
- `npm --prefix frontend run test:e2e` with approved unsandboxed execution: **1 Playwright shell test passed**, exit 0.
- Verification was frontend-local with synthetic fixtures. Live IdP/OIDC, production, Docker/PostgreSQL and remote CI are `NOT_VERIFIED` and outside this task.
- Tester made no product-code edits. Independent design/policy review remains pending under CHPMIS-007-R1.

