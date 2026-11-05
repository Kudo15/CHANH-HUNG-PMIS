# CHPMIS-027-R1 — Independent static review

## Identity and traceability

- **Task ID:** CHPMIS-027-R1
- **Role:** OpenCode independent read-only Reviewer.
- **Traceability:** CHPMIS-027, CHPMIS-027-T1, AC-14 preparation only, CHPMIS-011 R2 and mission §5–6.
- **Status:** COMPLETE — APPROVED, 0 P1/P2 and 3 non-blocking P3 notes; details in `.team/tasks/CHPMIS-027-R1-review-report.md`.
- **Required reads:** `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, `.team/tasks/CHPMIS-027-ac14-playwright-journey.md`, `.team/tasks/CHPMIS-027-T1-readonly-verification.md`, `.team/tasks/CHPMIS-027-T1-verifier-report.md`, `.team/tasks/CHPMIS-027-worker-report.md`, `.team/tasks/CHPMIS-011-runtime-approval-proposal.md`, `.team/tasks/CHPMIS-011-runtime-candidate-r2-review.md`, `.team/tasks/CHPMIS-023-isolated-synthetic-topology.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, `OPEN_QUESTIONS.md`, `frontend/package.json`, `frontend/playwright.chpmis011.config.ts`, `frontend/e2e/chpmis011-authenticated-journey.spec.ts`, `frontend/playwright.config.ts`, `frontend/vite.config.ts`, `backend/app/auth/routes.py`, `backend/app/auth/oidc.py`, and relevant project/auth policy source referenced by the journey.

## Objective and boundaries

Independently review the authored static assets, T1 evidence, strict scope and Verifier finding F1. Use only read-only source inspection; do not edit, run commands/tests, start services, access providers, credentials, DB, Registry, ports, browser, install dependencies, or attempt any denied command through another executable/wrapper. Do not treat lint/build failures as proof of authored-code correctness or runtime behavior. Do not pass AC-14.

## Review checklist

1. Check git status and scoped diff as read-only evidence; verify only four CHPMIS-027 allowlisted paths changed relative to task scope and preserve unrelated dirty work.
2. Assess test config: dedicated spec selection, loopback base URL and Vite port, API proxy target, unconditional no-reuse, Chromium, one worker/no retries, and no credential-bearing artifacts/reporting.
3. Assess journey: actual OIDC path, separate PM C/member D contexts, role and cookie attribute assertions without values, legitimate in-memory CSRF use, mixed UI/API qualification, project/task/dashboard/audit assertions, safe unauthenticated check, environment variable handling and sensitive-output suppression.
4. Adjudicate F1 from exact source/config: whether callback request uses the proxy origin or direct backend origin, how browser-binding cookies are scoped/set/sent, and whether the claimed mismatch is valid. Cite exact file:line and distinguish static inference from runtime proof.
5. Identify any supported P1/P2/P3 findings; return `APPROVED` or `CHANGES_REQUESTED`. No implementation changes.

## Reporting and DoD

Report required reads, scope, findings with severity/file:line, T1 evidence accurately, limitations, and verdict. Explicitly preserve lint/build as `NOT_VERIFIED`, E2E/runtime and AC-14 as `NOT_VERIFIED`. End with `SUMMARY: ...` and `ROLE_RESULT: done|review|blocked`. Coordinator reconciles the verdict into task register/ledger; CHPMIS-027 cannot close on a `CHANGES_REQUESTED` verdict. No Worker follow-up will be dispatched unless a review finding requires a scoped task and the required prompt template is verified.
