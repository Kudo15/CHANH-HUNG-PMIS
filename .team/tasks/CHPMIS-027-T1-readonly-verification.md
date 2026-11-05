# CHPMIS-027-T1 — Independent static verification

## Task identity

- **Task ID:** CHPMIS-027-T1
- **Role:** OpenCode read-only Tester/Verifier.
- **Traceability:** CHPMIS-027; AC-14 preparation only; CHPMIS-011 R2 and mission §5–6.
- **Status:** COMPLETE — Verifier report received; independent Reviewer dispatched next. No E2E/runtime evidence exists.
- **Required session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this task pack, `.team/tasks/CHPMIS-027-ac14-playwright-journey.md`, `.team/tasks/CHPMIS-027-worker-report.md`, `.team/tasks/CHPMIS-011-runtime-approval-proposal.md`, `.team/tasks/CHPMIS-011-runtime-candidate-r2-review.md`, `.team/tasks/CHPMIS-023-isolated-synthetic-topology.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, `frontend/package.json`, `frontend/playwright.chpmis011.config.ts`, `frontend/e2e/chpmis011-authenticated-journey.spec.ts`, `frontend/playwright.config.ts`, `frontend/e2e/shell.spec.ts`, `frontend/vite.config.ts`, `frontend/src/components/ProjectWorkbench.tsx`, `backend/app/auth/routes.py`, `backend/app/config.py`, `backend/app/projects/routes.py`, `backend/app/projects/schemas.py`, `backend/app/projects/service.py`, and `backend/app/auth/policy.py`. Report all required reads. Run `git status --short` and inspect the scoped diff read-only.

## Objective

Independently verify only the CHPMIS-027 static frontend assets, exact scope and Worker evidence. Run the three permitted static commands to observe current environment behavior. Do not run the E2E test or any service/provider/host action.

## Boundaries

- Read-only: do not edit any file, install/repair dependencies, inspect `.env` or credential values, start Vite/backend/Keycloak/Docker, make network requests, probe ports, access browser/provider/DB/Registry/account/ACL, commit, push, or alter permissions.
- Run only the exact commands listed below. If a command is denied or fails, record the exact output and exit code; do not try another executable, wrapper, shell, interpreter, dependency installation, or permission change.
- Explicitly distinguish a broken local lint/build dependency from a finding in the authored test. Do not claim TypeScript app build type-checks the new Playwright files if the TS config excludes them.
- `npm run test:e2e:chpmis011`, default Playwright E2E, and all runtime checks are forbidden in this task.

## Exact verification commands

From `frontend/`:

1. `npm run lint -- playwright.chpmis011.config.ts e2e/chpmis011-authenticated-journey.spec.ts`
2. `npm run build`

From repository root:

3. `git diff --check`

Do not add any command. Report exact output summary and exit code for each; if a command cannot run, mark `NOT_RUN`/`NOT_VERIFIED` and provide the observed denial/reason.

## Review checklist

- Only the allowed four CHPMIS-027 paths changed; default Playwright config/shell test and product/auth policy are untouched.
- Dedicated config uses only the CHPMIS-011 spec, port 25173, Vite webServer command `npm run dev -- --port 25173`, `API_PROXY_TARGET=http://127.0.0.1:28000`, unconditional `reuseExistingServer: false`, bundled Chromium, and artifacts disabled.
- Journey qualifies itself as mixed UI/API; PM C is positive actor; D is added using a browser-context request with legitimate CSRF in memory; UI creates project/task and checks dashboard/audit; credentials come only from named process env vars and are never logged.
- OIDC session/cookie assertions inspect attributes without values; no E2E execution or AC-14 pass claim.
- Worker run record timeout, GUI/session metadata, report's role result and ID discrepancy are reconciled by Coordinator; Tester reports what it observed independently.

## Reporting and DoD

Report required reads, exact scope, findings with file/line, commands/output/exit codes, limitations, and whether the assets satisfy the static task pack. Do not edit or close the task. End with `SUMMARY: ...` and `ROLE_RESULT: done|review|blocked`. Evidence is reconciled in `.team/tasks/CHPMIS-027-T1-verifier-report.md`; independent review is CHPMIS-027-R1. CHPMIS-027 and AC-14 remain open/NOT_VERIFIED until Tester and Reviewer requirements are met; any live journey is a separate Human Gate.
