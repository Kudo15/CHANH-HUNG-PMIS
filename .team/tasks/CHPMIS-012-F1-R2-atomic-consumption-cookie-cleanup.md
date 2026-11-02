# CHPMIS-012-F1-R2 — Atomic callback claim and cookie cleanup

- **Task ID:** CHPMIS-012-F1-R2
- **Role:** Hermes Worker (sole product-code writer)
- **Status:** READY_FOR_WORKER — coordinator follow-up after R1 review
- **Requirement trace:** CHPMIS-012 / mission §5; AC-05; `AGENTS.md`; `.team/CHARTER.md`; approved F1 task pack `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`; accepted route design `docs/superpowers/specs/2026-11-02-chpmis-012-f1-route-cookie-design.md`.
- **Prompt template:** Real prompts.chat Feature coding template by Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, retrieved through `.agents/skills/prompt-lookup` and recorded in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`. Modernization: first reproduce each gap with focused tests, make the smallest F1-only change, preserve existing auth/session policy and dirty work, then run only the checks listed below and report exact evidence.
- **Preceding state:** Worker run 110 is documented in `.team/tasks/CHPMIS-012-F1-worker-report.md`; independent R1 Reviewer card `t_bba958db` approved with 0 findings in `.team/tasks/CHPMIS-012-F1-independent-review.md`. Coordinator follow-up audit found gaps not covered by that review. Preserve all current workspace changes; do not clean, reset, stash, restore, or reinitialize.

## Objective

Complete the already approved F1 one-time OIDC transaction behavior in three narrow areas:

1. Make transaction consumption an atomic database claim so among callbacks that have already loaded the same valid state, exactly one can consume it and reach token exchange. A callback that loses the claim must fail closed before exchange. Preserve the current required behavior that missing or mismatched browser binding does not consume Browser A's valid transaction.
2. Clear the browser-binding cookie whenever this callback successfully consumes its transaction, including downstream token exchange, ID-token validation, inactive-user, and session-creation failure paths. Do not clear it for unknown state, missing/mismatched binding, expired/legacy rejection before consumption, or a failed atomic claim.
3. Add a positive local mocked-HTTP regression asserting that `DefaultOIDCClient` includes a supplied `code_verifier` in the token request body. The production implementation already appears to do this, so the coverage test may pass at baseline; record that without altering correct production behavior.

No schema or migration change is needed or authorized in this follow-up.

## Allowed files

Modify only:

- `backend/app/auth/oidc.py`
- `backend/app/auth/routes.py`, only for F1 callback cookie cleanup coordination
- `backend/tests/test_auth_oidc.py`
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md`

Do not modify migrations, models, config, other tests, other routes, frontend, Compose, Keycloak, dependencies, or unrelated dirty files. If any additional file or policy change is required, stop and request a scoped update.

## Required implementation and tests

- Write focused RED tests for the atomic-consumption and cookie-cleanup behavior gaps before changing implementation. The default token-body verifier item is a coverage-only gap: add its positive regression test and run it against current code first. If the current implementation passes, record that baseline pass and do not alter correct verifier behavior just to manufacture RED.
- Use an atomic conditional database delete/claim after validating expiry and browser binding. Check that exactly one row was affected before committing and before invoking token exchange. A stale concurrent reader must not get a second exchange.
- Keep the raw browser token out of storage and logs. Preserve constant-time binding comparison, exact callback URI, S256 PKCE, one-time consumption before remote exchange, existing signed-token validation, session and CSRF behavior.
- Coordinate the route with the service so the cookie is cleared after a successful consumption even if later callback processing fails. Keep the cookie on pre-consumption validation failures, especially missing/mismatched binding. Preserve the existing callback HTTP status/detail behavior where possible; do not leak exception internals or auth secrets.
- Cover a deterministic stale-reader/two-claim regression and assert at most one token exchange; cover cookie clearing after a consumed transaction on downstream failure and cookie retention after rejected binding; add the positive verifier-body assertion. Do not add a `code_verifier=None` omission case or alter `DefaultOIDCClient` behavior.
- No live database service, HTTP provider, Keycloak, browser, or Docker is needed for this task.

## Verification

From `backend/`:

1. `.venv\Scripts\python.exe -m pytest -q tests/test_auth_oidc.py`
2. `.venv\Scripts\python.exe -m pytest -q`
3. `.venv\Scripts\ruff.exe check . ../dev`
4. `.venv\Scripts\ruff.exe format --check app/auth/oidc.py app/auth/routes.py tests/test_auth_oidc.py`

From repository root:

5. `git diff --check`

Do not run mutating formatters or inspect environment variables. Report every exact command, CWD, summary, and exit code. Include PostgreSQL as `NOT_REQUIRED` because this follow-up changes no schema or migration.

## Definition of Done

- Atomic-consumption and cookie-cleanup behavior gaps are shown RED before implementation and GREEN after. The positive verifier-body regression is added and recorded; because production propagation already exists, it may pass at baseline without a code change.
- The exact allowlist is respected and all listed checks are reported truthfully.
- `.team/tasks/CHPMIS-012-F1-R2-worker-report.md` records Task ID, Worker role, scope, DoD, requirement trace, real template, changed files, test evidence and remaining limits.
- Worker requests independent review and does not declare F1 or the platform gate complete.
- No commit, stage, push, deploy, secret output, unrelated edits, or forbidden git discard command.
