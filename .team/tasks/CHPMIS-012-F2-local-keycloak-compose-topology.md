# CHPMIS-012-F2 — Local Keycloak Compose and browser/backchannel topology

- **Task ID:** CHPMIS-012-F2
- **Role:** Hermes Worker (sole product/config writer), then OpenCode read-only Tester and separate Hermes Reviewer.
- **Status:** COMPLETE — local configuration scope only. Worker run 103 and Coordinator exact checks passed; independent Hermes Reviewer `t_57d8ae5a`/run 104 returned `APPROVED` with zero P1/P2/P3 findings. OpenCode run `2026-11-02T01-08-45-verifier-chpmis-012-f2-read-only-config-verificat-170b` reached GUI session `ses_e6632c57dffeZ27K2snFHyENTG` but the configured provider returned HTTP 402 before any check (`NOT_VERIFIED`). Live Keycloak/browser/login, production, and OpenCode verification remain unverified. Evidence: `.team/tasks/CHPMIS-012-F2-coordinator-evidence.md` and `.team/tasks/CHPMIS-012-F2-independent-review.md`.
- **Trace:** CHPMIS-012 / mission §5; AC-05; approved synthetic-only Keycloak profile in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`; current `compose.yaml`, `.env.example`, `dev/keycloak/realm.json`, and `frontend/vite.config.ts`.
- **Prompt template:** Real prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, located/retrieved via `.agents/skills/prompt-lookup` and cited in `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`. Modernized for a local configuration Worker: inspect current profile and realm; make only allowlisted config changes; keep all services loopback-only and secrets as placeholders; test Compose interpolation; report exact evidence and risks. Do not alter application authentication logic, start services, change harness permissions, or access external/production providers.
- **Baseline:** Existing dirty branch `audit-remediation/verify-audit-findings`; baseline SHA `7a27930bd3f80d4d08bcf9ed55ae829c90ca7637`. Preserve all existing workspace changes. Run in the current checkout; no commit/stage/push/deploy.

## Objective

Wire only the opt-in `local-oidc` Compose topology so the browser uses Keycloak's fixed loopback frontend issuer/auth endpoint while backend token/JWKS calls use the Compose service DNS name. Proxy frontend `/api/*` calls to backend in both native-dev default and Compose. Restrict the synthetic Keycloak client redirect allowlist to the exact fixed backend callback URI and remove wildcard web origins/redirects. Keep all published ports on `127.0.0.1` and all credentials as `.env.example` placeholders.

## Allowed files

Modify only:

- `compose.yaml`
- `.env.example` (names and placeholders only; never real secrets)
- `frontend/vite.config.ts`
- `dev/keycloak/realm.json`
- Append-only `.team/tasks/CHPMIS-012-F2-worker-report.md`

No backend/frontend application code, dependencies, tests outside the listed command, CI workflows, runbooks, migrations, authorization policy, real credentials, service startup, or unrelated files. If current Compose service structure prevents safe configuration inside this allowlist, stop and ask for a scope update.

## Required configuration

1. Backend environment must map existing settings names for `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_AUTHORIZATION_ENDPOINT`, `OIDC_TOKEN_ENDPOINT`, `OIDC_JWKS_URI`, and `OIDC_REDIRECT_URI` to safe local synthetic defaults. The frontend-visible issuer/auth endpoint and the private Compose `keycloak:8080` token/JWKS endpoints must be distinct where needed; token `iss` verification still uses the fixed public issuer. Keep defaults usable with the existing Compose config validation; never require real credentials for config parsing.
2. Vite dev proxy forwards `/api` to `API_PROXY_TARGET` defaulting to loopback backend `http://127.0.0.1:8000`; Docker frontend retains internal `http://backend:8000` override. Preserve `/health` proxy and loopback bind.
3. Keycloak client remains confidential and standard authorization-code only; keep implicit flow disabled. Redirect allowlist must contain only the exact fixed callback `http://127.0.0.1:8000/api/v1/auth/callback`; remove `http://127.0.0.1:5173/*`. Remove wildcard web origin; no CORS wildcard is required for backend code exchange.
4. Do not disable Secure cookies, CSRF, signed-token verification, issuer/audience checks, or change `KC_HOSTNAME`/backchannel dynamic behavior without testable evidence. Do not add frontend redirect patterns or open redirect configuration.
5. `.env.example` contains placeholders only. Never print/read an existing root `.env` or change it.

## Verification commands

From repository root, run exactly:

1. `docker compose --env-file .env.example --profile local-oidc config --quiet`
2. `git diff --check`

From `frontend/`, run only if no package/test/dependency edits were needed and Vite config validation is provided by the repository; do not invent a new command. Worker must report command cwd, output summary and exit code. Config validation is not evidence that Keycloak starts or login works.

## Definition of Done

- Compose and Vite configuration match the fixed local browser/backchannel topology; Keycloak callback allowlist has no wildcard.
- All exposed host bindings remain loopback-only; no real credential or agency data is added.
- Exact listed checks and scoped diff reported.
- Worker requests review; no live provider/browser/DB or production acceptance claim.
- OpenCode Tester independently inspects config/checks if its configured provider is available; any failure is NOT_VERIFIED without permission changes.
- Separate Hermes Reviewer approves the full scoped diff with zero blocking findings.
