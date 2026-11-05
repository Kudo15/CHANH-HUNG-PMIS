# CHPMIS-027 — Isolated authenticated Playwright journey asset

## Identity and authority

- **Task ID:** CHPMIS-027
- **Role sequence:** OpenCode Worker → OpenCode read-only Tester → independent Reviewer.
- **Traceability:** AC-14; CHPMIS-011/012-F1/F2/016/023; mission §5–6.
- **Status:** COMPLETE for static asset authoring. Worker and Tester evidence are recorded; independent Reviewer APPROVED with 0 P1/P2 and 3 non-blocking P3 notes. Tester lint/build remain `NOT_VERIFIED`, `git diff --check` exit 0. Reviewer rejected F1 as a static inference error; loopback Secure-cookie behavior remains a runtime prerequisite. AC-14, live runtime, provider login and E2E execution remain `NOT_VERIFIED` and gated.
- **Required session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this pack, `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `.team/tasks/CHPMIS-011-runtime-approval-proposal.md` including R2 decisions, `.team/tasks/CHPMIS-011-runtime-candidate-r2-review.md`, `.team/tasks/CHPMIS-023-isolated-synthetic-topology.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, `frontend/package.json`, `frontend/playwright.config.ts`, `frontend/vite.config.ts`, `frontend/e2e/shell.spec.ts`, `frontend/src/App.tsx`, `frontend/src/components/ProjectWorkbench.tsx`, `backend/app/auth/routes.py`, `backend/app/projects/routes.py`, `backend/app/projects/schemas.py`, and `backend/app/auth/policy.py`. Run `git status --short` before edits and preserve every existing change.

## Prompt template

- **Real template:** prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`.
- **Source:** Previously searched/retrieved through the installed `.agents/skills/prompt-lookup` skill and recorded in `.team/tasks/CHPMIS-023-isolated-synthetic-topology.md` and its Worker report. Reuse that exact template; do not invent a replacement or change model/provider.
- **Adapted Worker prompt:** “Use the Feature coding template as a bounded frontend test Worker for CHPMIS-027. Add a dedicated Playwright configuration and one authenticated synthetic PM journey using the actual OIDC redirect, then the existing project UI plus the reviewed browser-context member API step. Use PM C as the positive actor and synthetic Member D as the assignee; assert Secure/HttpOnly session-cookie attributes and successful authenticated requests without printing cookie, CSRF, OIDC, or credential values. Set the dedicated base URL to `http://127.0.0.1:25173`, Vite command to `npm run dev -- --port 25173`, `API_PROXY_TARGET=http://127.0.0.1:28000`, and `reuseExistingServer: false`. Keep the existing default Playwright config/test untouched. Do not change product/auth/workflow code, invent the role fixture, inspect `.env`, start services, access Keycloak, run the E2E command, or bypass a denied check. Run only the listed static lint/build/diff checks; report the E2E and runtime prerequisites as NOT_VERIFIED. Preserve unrelated dirty work and stop at any scope ambiguity.”

## Objective and exact write scope

Prepare a separate Playwright test asset for the mixed UI/API authenticated AC-14 journey accepted for further planning by CHPMIS-011 R2. Create/modify only:

1. `frontend/playwright.chpmis011.config.ts` — dedicated test config; do not modify `frontend/playwright.config.ts`.
2. `frontend/e2e/chpmis011-authenticated-journey.spec.ts` — one test for PM C's authenticated journey.
3. `frontend/package.json` — add a separate script such as `test:e2e:chpmis011` that selects only the dedicated config; do not replace or change existing scripts.
4. `.team/tasks/CHPMIS-027-worker-report.md` — append-only report.

No product source, auth/policy/workflow behavior, backend, realm/Compose topology, role fixture, dependencies/lockfiles, CI, default Playwright config, runbook, acceptance/ledger, or other path is in scope. No install, service lifecycle, provider access, database/Registry/account/ACL action, port probe, commit/push/deploy, or permission change.

## Journey and configuration contract

- Dedicated config: `testDir: './e2e'`, select only `chpmis011-authenticated-journey.spec.ts`; base URL `http://127.0.0.1:25173`; web server command `npm run dev -- --port 25173`; set only `API_PROXY_TARGET=http://127.0.0.1:28000`; `reuseExistingServer: false` unconditionally; bundled Chromium; one worker; no retries; explicitly disable trace/video/screenshots and use a terse reporter that cannot emit credentials or callback values. Preserve existing `playwright.config.ts` and `shell.spec.ts` behavior.
- Login in each fresh browser context through the actual `/api/v1/auth/login` redirect to the synthetic Keycloak realm at `http://127.0.0.1:28081`; do not fake sessions or bypass OIDC, state, nonce, PKCE, browser-binding, CSRF, or cookie validation. Complete browser login as PM C and Member D in separate contexts. Runtime accounts/local users and the test-only global role fixture are prerequisites for a later explicitly gated run; this Worker does not provision or modify any identity/role.
- Read only process environment variables `CHPMIS011_PM_USERNAME`, `CHPMIS011_PM_PASSWORD`, `CHPMIS011_MEMBER_USERNAME`, and `CHPMIS011_MEMBER_PASSWORD` when the future E2E command is invoked. If missing, fail with a message naming missing variable names only; do not skip or print values. Never read `.env` files, put credentials in command arguments, or print/log usernames, passwords, codes, tokens, CSRF values, cookies, full callback URLs, or response bodies that could contain them.
- Assert PM C's authenticated session and exact synthetic global role `project_manager`, and Member D's session and role `member`; inspect session response only in memory. Assert session cookie exists with Secure, HttpOnly and SameSite=Lax attributes and CSRF cookie exists with Secure, non-HttpOnly and SameSite=Lax; assert a successful authenticated request. Never inspect or print cookie values.
- As PM C, create a uniquely named synthetic project through the UI. Add D through `POST /api/v1/projects/{project_id}/members` from the same authenticated browser context using the actual session cookie and legitimate CSRF cookie value in memory; label the test/report as a mixed UI/API journey, not a staff-assignment UI test. Refresh project state, create a task in the UI assigned to D, transition it through the existing UI, and assert the project dashboard count and audit history reflect the task/project actions as PM C.
- Include one safe unauthenticated negative check (for example, `/api/v1/auth/session` returns 401 before login). Do not invent role semantics. Invalid/replayed/swapped state/binding, inactive-user and role/scope denial cases are explicitly deferred to a follow-up task; this pack does not claim those negative cases.
- This test must not be run by Worker or Tester. It starts Vite and reaches Keycloak/backend and requires a later explicit runtime/provider Human Gate plus separately prepared isolated services and fixture. No evidence from this task can pass AC-14.

## Verification commands

From `frontend/`, these existing commands are permitted for Worker and Tester:

1. `npm run lint -- playwright.chpmis011.config.ts e2e/chpmis011-authenticated-journey.spec.ts`
2. `npm run build`

From repository root:

3. `git diff --check`

Do not install dependencies or run `npm run test:e2e:chpmis011`, `npm run test:e2e`, Playwright, a dev server, a backend, Keycloak, Docker, database commands, or any live/browser/provider action. If a permitted command is denied or unavailable, record exact reason and `BLOCKED`/`NOT_VERIFIED`, with no alternate command or permission workaround.

## Worker/Tester/Reviewer DoD

- Worker changes only the exact allowlist; reports RED/GREEN where a non-runtime static test can safely exercise the authored asset, exact permitted commands/output/exit codes, and all unrun live evidence. E2E command is not run.
- Read-only Tester independently reviews the scoped diff and runs only the three listed static commands; no edits or E2E execution.
- Independent Reviewer returns `APPROVED` or `CHANGES_REQUESTED` with file/line and P1/P2/P3 findings; checks base/proxy/callback/no-reuse, secret and browser-artifact handling, mixed UI/API qualification, and strict scope.
- CHPMIS-027 may close for asset authoring after Worker/Tester/Reviewer DoD, while AC-14 remains NOT_VERIFIED pending later role fixture, isolated runtime, owner Human Gate, and live authenticated journey evidence.

## Evidence reconciliation (2026-11-05)

- Worker run timed out after writing assets/report; run/session metadata reconciled in the ledger. Worker reported lint exit 2, build exit 1, and diff check exit 0.
- T1 run `2026-11-05T06-55-26-verifier-chpmis-027-t1-static-frontend-verificati-07d4`, session `ses_e55824abbffewhOGD8UIyOGeZJ`, GUI listed: lint exit 1 and build exit 1 remain `NOT_VERIFIED` due local ESLint/Vite dependency failures; `git diff --check` exit 0. E2E/runtime not run. Full report: `.team/tasks/CHPMIS-027-T1-verifier-report.md`.
- R1 run `2026-11-05T07-22-58-reviewer-chpmis-027-r1-independent-static-review-ac5e`, session `ses_e556913b6ffeJeu65fKj0YISoQ`, GUI listed, driver exit 0, cost 0, model/provider not exposed; APPROVED, 0 P1/P2 and three P3 notes. F1 was rejected statically because host-only cookies are port-agnostic for the shared loopback host. Full report: `.team/tasks/CHPMIS-027-R1-review-report.md`.
- Reconciled metadata discrepancy: Worker says lint exit 2, T1 says exit 1. Neither result establishes lint correctness; both remain `NOT_VERIFIED`.
- Acceptance `AC-14` remains `NOT_VERIFIED`. No live flow or secure-cookie-on-loopback result is claimed.

## Reporting format

Each role records Task ID, role, exact scope, requirement trace, prompt template where applicable, run/session ID, GUI visibility, model/provider/cost only when observed, exact commands and exit codes, changes/evidence, blockers, and conclusion. Worker report ends with `SUMMARY: ...` and `ROLE_RESULT: done|review|blocked`.
