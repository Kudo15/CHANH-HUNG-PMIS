# CHPMIS-012-F1 Route Cookie Integration Design

**Status:** Owner approved the minimal route extension on 2026-11-02 in response to the scope clarification. This extends the approved F1 task pack only at the HTTP cookie boundary.

## Intent

Complete the approved browser-bound OIDC transaction design. The service already owns PKCE/state/nonce transaction logic, but the current FastAPI route layer is the HTTP boundary that can set a cookie on the login redirect and read a cookie from the callback request.

## Current behavior

`backend/app/auth/routes.py` calls `initiate_login(db, settings)` and returns a `RedirectResponse`. The callback receives a `Request`, calls `process_callback(...)` without the browser's transaction cookie, and then constructs a JSON response for the existing session and CSRF cookies. The OIDC service cannot explicitly set or read browser cookies unless the route passes those HTTP values.

## Approaches considered

1. **Minimal explicit route integration — chosen by the owner.** Add only `routes.py` to F1's allowlist for setting the short-lived binding cookie on `/login`, passing the callback cookie value into OIDC validation, and clearing it when the transaction is consumed. This keeps cookie policy at the existing HTTP boundary and preserves the existing service/session design.
2. **Middleware or another application-wide hook.** This would touch additional files and broaden the task beyond the F1 allowlist; it is not selected.
3. **Implicit frame access, monkey-patching, or call-stack inspection.** These bypass explicit APIs and are unsafe; they are forbidden.

## Scope and constraints

- Add `backend/app/auth/routes.py` to the existing F1 allowlist only for explicit binding-cookie set/pass/clear integration.
- Keep the remaining F1 scope unchanged: PKCE S256, random verifier, browser-binding digest, strict callback/state/nonce/issuer/audience checks, one-time atomic transaction consumption, one additive nullable migration after 0006, and listed tests.
- The binding cookie remains Secure, HttpOnly, SameSite=Lax, short-lived and root-path scoped; never store its raw value in the database or logs.
- Preserve existing session and CSRF cookie behavior, authorization policy, public response contracts, and all other routes.
- No frontend, Compose/Keycloak, dependency, production, external provider, or unrelated file changes.

## Implementation details left to the Worker

Choose the smallest explicit return/API shape that carries the authorization URL and one-time cookie value from the OIDC helper to the `/login` response. Pass the callback cookie value directly from `Request.cookies` into transaction validation. Clear the binding cookie only as part of the existing callback transaction lifecycle, using the same cookie attributes. Keep error responses and session creation consistent with the task pack. Do not use implicit context access.

## Verification and ownership

Use the exact commands in `.team/tasks/CHPMIS-012-F1-browser-bound-pkce-transaction.md`, including the added `routes.py` file in the scoped Ruff format command. Worker must demonstrate RED/GREEN, preserve the shared PostgreSQL test file, request independent review, and not claim a live IdP or browser E2E.
