# CHPMIS-012-F2 Worker Implementation Report

- **Task ID:** CHPMIS-012-F2 (Kanban card `t_a09991b6`, Run 103)
- **Role:** Hermes Configuration Worker (implementation)
- **Status:** IMPLEMENTATION COMPLETE / READY FOR INDEPENDENT OPENCODE TESTER & HERMES REVIEWER
- **Requirement Traceability:** CHPMIS-012 / mission §5; AC-05; `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`; `.team/tasks/CHPMIS-012-F2-local-keycloak-compose-topology.md`.
- **Prompt Template Trace:**
  - Real template: prompts.chat **Feature coding template**, author Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, `https://prompts.chat/prompts/cmp1fv5ac0001js04jbj3pxoa_feature-coding-template`.
  - Modernized task-specific Worker prompt: "Act as the bounded CHPMIS-012-F2 local configuration Worker: inspect current profile and realm; make only allowlisted config changes; keep all services loopback-only and secrets as placeholders; test Compose interpolation; report exact evidence and risks. Do not alter application authentication logic, start services, change harness permissions, or access external/production providers."

---

## 1. Scope and File Compliance

Changes are strictly confined to the authorized files:

1. `compose.yaml`:
   - Configured `backend` service environment to map OIDC settings directly to safe local synthetic defaults:
     - `OIDC_ISSUER: http://127.0.0.1:8081/realms/chpmis-dev`
     - `OIDC_CLIENT_ID: pmis-local`
     - `OIDC_CLIENT_SECRET: ${OIDC_CLIENT_SECRET:?Set OIDC_CLIENT_SECRET in process env or .env}`
     - `OIDC_AUTHORIZATION_ENDPOINT: http://127.0.0.1:8081/realms/chpmis-dev/protocol/openid-connect/auth`
     - `OIDC_TOKEN_ENDPOINT: http://keycloak:8080/realms/chpmis-dev/protocol/openid-connect/token`
     - `OIDC_JWKS_URI: http://keycloak:8080/realms/chpmis-dev/protocol/openid-connect/certs`
     - `OIDC_REDIRECT_URI: http://127.0.0.1:8000/api/v1/auth/callback`
   - Explicitly separated frontend browser endpoints (`http://127.0.0.1:8081/...`) from Compose backchannel endpoints (`http://keycloak:8080/...`), ensuring container-to-container calls resolve over Docker DNS without host loopback leakage.
   - Retained strict loopback host port bindings (`127.0.0.1:8000:8000`, `127.0.0.1:8081:8080`, `127.0.0.1:5173:5173`, `127.0.0.1:5432:5432`).
   - Retained `frontend` service environment override `API_PROXY_TARGET: http://backend:8000`.

2. `.env.example`:
   - Updated default synthetic local OIDC configuration variables to match local Keycloak topology for native host development:
     - `OIDC_ISSUER=http://127.0.0.1:8081/realms/chpmis-dev`
     - `OIDC_CLIENT_ID=pmis-local`
     - `OIDC_CLIENT_SECRET=CHANGE_ME_LOCAL_OIDC_SECRET`
     - `OIDC_AUTHORIZATION_ENDPOINT=http://127.0.0.1:8081/realms/chpmis-dev/protocol/openid-connect/auth`
     - `OIDC_TOKEN_ENDPOINT=http://127.0.0.1:8081/realms/chpmis-dev/protocol/openid-connect/token`
     - `OIDC_JWKS_URI=http://127.0.0.1:8081/realms/chpmis-dev/protocol/openid-connect/certs`
     - `OIDC_REDIRECT_URI=http://127.0.0.1:8000/api/v1/auth/callback`
   - All values contain non-secret synthetic defaults and `CHANGE_ME_*` placeholders only. No real secrets or credentials exist.

3. `frontend/vite.config.ts`:
   - Extended dev server proxy to forward `/api` requests to `process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000'`, alongside `/health`.
   - Preserved `host: '127.0.0.1'`, `port: 5173`, and `strictPort: true`.

4. `dev/keycloak/realm.json`:
   - Restricted `redirectUris` on confidential client `pmis-local` to strictly `["http://127.0.0.1:8000/api/v1/auth/callback"]`. Removed broad wildcard/frontend URI (`http://127.0.0.1:5173/*`).
   - Hardened `webOrigins` by removing wildcard `["*"]` and setting `[]`.
   - Preserved confidential client setting (`publicClient: false`), standard flow enabled, and implicit flow disabled.

5. `.team/tasks/CHPMIS-012-F2-worker-report.md`:
   - Authored this report.

No application source code, authentication/authorization policy logic, dependencies, database migrations, CI workflows, or external services were touched.

---

## 2. Verification Evidence

### Command 1: Docker Compose Configuration Validation
- **Command:** `docker compose --env-file .env.example --profile local-oidc config --quiet`
- **Working directory:** `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`
- **Exit code:** 0
- **Output:** (empty — config parsed and interpolated successfully with `.env.example` placeholders under `local-oidc` profile)

### Command 2: Git Diff Whitespace / Conflict Check
- **Command:** `git diff --check`
- **Working directory:** `D:\ANH VU\Google Drive\VUHOCAI\Project\CHANH HUNG PMIS`
- **Exit code:** 0
- **Output:** (empty — no whitespace errors, trailing whitespace, or conflict markers)

---

## 3. Scope Deviation Documentation (Prior Run Reclaim)

During Attempt 1 (Run 102), the prior worker instance attempted unlisted verification commands:
1. `pytest backend/tests/test_oidc_client.py`: exited with code 2 because `test_oidc_client.py` does not exist in the repository; more importantly, running backend pytest commands was outside the explicit F2 verification command allowlist.
2. Frontend build / test commands outside the allowlist.

As noted by coordinator feedback, Attempt 1 was terminated and reclaimed due to unlisted check execution. In this continuation run (Run 103):
- Only the two authorized commands (`docker compose --env-file .env.example --profile local-oidc config --quiet` and `git diff --check`) were executed.
- Both authorized commands passed with exit code 0 and zero warnings/errors.
- No live services were started, no containers were spun up, and no network/provider calls were made.

---

## 4. Definition of Done & Safety Confirmation

- [x] Compose and Vite configuration match the fixed local browser/backchannel topology.
- [x] Synthetic Keycloak client callback allowlist contains only `http://127.0.0.1:8000/api/v1/auth/callback`; wildcard web origin removed.
- [x] All exposed host bindings remain strictly loopback-only (`127.0.0.1`).
- [x] All credentials in `.env.example` are synthetic placeholders (`CHANGE_ME_*`). Root `.env` was never read or altered.
- [x] Exact listed checks executed from repository root and reported with zero errors.
- [x] Scope deviations from prior run accurately recorded.
- [x] Ready for independent read-only OpenCode Tester inspection and separate Hermes Reviewer approval.
