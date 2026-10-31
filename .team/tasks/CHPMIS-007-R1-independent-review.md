# CHPMIS-007-R1 — Independent Review

## Task identity and role

- **Task ID:** CHPMIS-007-R1
- **Role:** Independent Reviewer, read-only (Hermes CLI Kanban; explicit dispatch after Worker and Tester)
- **Prompt template:** `Senior Code Reviewer (severity-ranked)`, prompts.chat ID `cmv9n79m30005ku060pzornri`, retrieved via `.agents/skills/prompt-lookup/` and adapted to this feature. Source: https://prompts.chat/prompts/cmv9n79m30005ku060pzornri_senior-code-reviewer-severity-ranked
- **Harness:** Active Hermes `default` profile; no model/provider/effort override.
- **Workspace:** Existing project directory `dir:D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`; separate card after Worker and Tester complete.

## Objective and review scope

Review only CHPMIS-007's changed frontend files and evidence against the task pack, design spec, approved access/workflow policies, and relevant existing API contracts. Treat existing dirty files outside the CHPMIS-007 allowlist as baseline and do not modify them. Do not run implementation or create files.

Prioritize:

1. Unauthorized project fetches, project scope and cross-project aggregate leakage.
2. Correct project role derived from membership and server-authoritative enforcement.
3. CSRF/cookie handling, session token storage, and protected error disclosure.
4. Exact task transition matrix, assignment restrictions, archive confirmation and read-only lifecycle.
5. Mutation payload/route compatibility, stale state, and reliable error/refresh behavior.
6. Accessible/responsive states and meaningful tests for mutations and policy boundaries.
7. Scope drift into backend, schema, policy, dependencies, secrets, or unrelated files.

## Required report

List findings first, severity-ranked P1/P2/P3 with precise file and line evidence; distinguish confirmed defects from optional improvements. If no findings, state explicitly what contracts, policy boundaries and tests were examined. Return `APPROVED` only when no actionable scoped finding remains; otherwise `CHANGES_REQUESTED`. Do not claim legal, production, IdP, Docker, or live database validation. Reviewer makes no edits.

### Modernized Reviewer prompt

Using the retrieved Senior Code Reviewer template, independently review only the CHPMIS-007 frontend changes and Tester evidence against the task pack, design, approved user roles/workflow, and existing route/schema contracts. Treat other modified/untracked files as pre-existing baseline. Inspect without editing; prioritize authorization scope, selected-project role derivation, CSRF/cookie handling, exact transition controls, assignment constraints, archived read-only state, audit/dashboard exposure, mutation route compatibility, failure handling, accessibility, test gaps, and allowlist drift. Return only evidenced P1/P2/P3 findings with tight file:line references followed by `APPROVED` or `CHANGES_REQUESTED`; separate optional improvements. No legal, production, IdP, Docker or database claims.

## Observed result — 2026-10-30

- **Verdict:** APPROVED; no findings (zero P1/P2/P3). One optional future styling improvement: standardize remaining raw `<button>` elements with the existing UI primitive.
- **Run:** Hermes CLI Kanban card `t_0ecaffc1`, run #26, active profile `default`, worker session `20261030_162700_d8c17a`; model/provider/cost/token counts not exposed in run metadata; GUI visibility not observed.
- **Independent checks:** Vitest 15/15, ESLint 0 diagnostics, TypeScript/Vite build, Playwright E2E 1 passed; all exit 0 per run metadata.
- **Review coverage:** All ten task acceptance criteria and seven review focus areas; no source edits.
- **Limits:** No live IdP/OIDC, production, Docker/PostgreSQL, or remote CI validation.

