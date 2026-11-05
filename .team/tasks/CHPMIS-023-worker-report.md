# CHPMIS-023 — Worker Report (append-only)

## Entry 1 — initial preparation — 2026-11-04 (session date)

- **Task ID:** CHPMIS-023; **role:** OpenCode Worker (bounded synthetic configuration, no runtime).
- **Trace:** CHPMIS-011/012-F2, AC-05/14, mission §5–6.
- **Harness/model:** OpenCode Desktop session (this session); model `Auto: coding` (ID `auto:coding`), provider FreeLLMAPI as approved and selected for this Worker session (observed provider ID `openai-completions`); profile/effort NOT_EXPOSED. No provider or model change was made.
- **Prompt template:** prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, previously located/retrieved via the installed `prompt-lookup` skill (recorded in CHPMIS-011 pack, 2026-10-31, and in this pack line 8), adapted per pack: bounded synthetic configuration Worker, two isolated loopback-only Compose/realm files, no real credentials, config-only checks, full limitation disclosure, no service start, no auth-behavior change, no commit, no edits outside the allowlist.
- **Session-start reads (all completed):** `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this pack (`.team/tasks/CHPMIS-023-isolated-synthetic-topology.md`), `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `.team/tasks/CHPMIS-011-runtime-approval-proposal.md`, `.team/tasks/CHPMIS-011-runtime-candidate-r2-review.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, `compose.yaml`, `dev/keycloak/realm.json`, `.env.example` (read-only; used only as the explicitly selected env file for the config parse). `git status` inspected before edits.
- **Session-start `git status --porcelain=v1 -b`:** branch `audit-remediation/verify-audit-findings`; 15 pre-existing modified tracked files and 24 pre-existing untracked paths (including this pack and prior task docs) were observed and preserved; none were touched by this Worker.

## Exact write scope (files created by this Worker)

1. `dev/keycloak/compose.chpmis011-isolated.yaml` — standalone Compose file with only an isolated `db` (PostgreSQL) service and `keycloak` service; no backend/frontend services or ports; no inheritance from root `compose.yaml`.
2. `dev/keycloak/realm.chpmis011-isolated.json` — four-user non-secret synthetic realm variant based on the current reviewed realm.
3. `.team/tasks/CHPMIS-023-worker-report.md` — this append-only report.

No other path was created or modified (confirmed by post-edit `git status`; the modified-file set is byte-identical to session start; only the two config files are new under `dev/keycloak/`).

## Configuration contract compliance (source inspection — static, not runtime proof)

### `dev/keycloak/compose.chpmis011-isolated.yaml`

- Standalone: only `db` and `keycloak` services; root Compose `ports` lists are not inherited (standalone file, not an override); no backend/frontend service or port.
- `db`: image `postgres:17-bookworm` (matches existing); sole published binding `"127.0.0.1:25432:5432"`; data in new **project-scoped** named volume `chpmis011_isolated_pgdata` (declared in top-level `volumes:`, not `external`, not the existing `pgdata`); preserves existing interpolation names `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` with `:?` required process-supplied password (no default); healthcheck preserved verbatim from the reviewed root file.
- `keycloak`: image `quay.io/keycloak/keycloak:26.8.1` (matches existing); sole published binding `"127.0.0.1:28081:8080"`; `KC_HOSTNAME: http://127.0.0.1:28081`; retained reviewed behavior: `profiles: [local-oidc]`, `command: start-dev --import-realm --health-enabled=true`, `JAVA_OPTS_APPEND: -Dkeycloak.migration.replace-placeholders=true`, `KC_HOSTNAME_BACKCHANNEL_DYNAMIC: "true"`, `KC_HTTP_PORT: 8080`, `KC_HEALTH_ENABLED: "true"`; realm file mounted **read-only**: `./realm.chpmis011-isolated.json:/opt/keycloak/data/import/realm.json:ro`.
- Credentials are environment placeholders only: `KC_BOOTSTRAP_ADMIN_PASSWORD`, `OIDC_CLIENT_SECRET`, `KC_SYNTHETIC_ADMIN1_PASSWORD`, `KC_SYNTHETIC_ADMIN2_PASSWORD` (required, matching the reviewed root file), plus `KC_SYNTHETIC_PM_PASSWORD` and `KC_SYNTHETIC_MEMBER_PASSWORD` (required, no defaults) for the new C/D users. No literal credentials anywhere in the file.
- Header comment states DESIGN ONLY / NOT APPROVED FOR EXECUTION, loopback-only intent, that `chpmis023config` is a config-rendering-only project name, and that the real runtime must select a unique project and stop if the project/volume/ports already exist.
- Static verification (read-only script, no temp files): CR=0 / LF=54, 0 trailing-whitespace lines; exactly two `127.0.0.1:` port bindings (25432, 28081); one `:ro` mount.

### `dev/keycloak/realm.chpmis011-isolated.json`

- Realm/client identity preserved from the current reviewed realm: `realm: chpmis-dev`, `clientId: pmis-local`, same enabled/ssl/registration flags, same client auth-protocol semantics (`publicClient: false`, `standardFlowEnabled: true`, `implicitFlowEnabled: false`, `directAccessGrantsEnabled: true`, `serviceAccountsEnabled: false`), same `department-mapper` protocol mapper, `secret: ${OIDC_CLIENT_SECRET}` (environment placeholder).
- **Sole** client redirect URI: exactly `http://127.0.0.1:28000/api/v1/auth/callback`; no `8000` callback, no wildcard, `webOrigins: []`.
- Four synthetic users only, no real records:
  - A: `synthetic-admin-1` (unchanged identity from reviewed realm; `${KC_SYNTHETIC_ADMIN1_PASSWORD}`);
  - B: `synthetic-admin-2` (unchanged identity from reviewed realm; `${KC_SYNTHETIC_ADMIN2_PASSWORD}`);
  - C: `synthetic-pm-1` — clearly named project-manager test user; `${KC_SYNTHETIC_PM_PASSWORD}`;
  - D: `synthetic-member-1` — clearly named member test user; `${KC_SYNTHETIC_MEMBER_PASSWORD}`.
- **No static identity receives a global application role**: the file contains no `roles`, no `clientRoles`, no realm/client role assignment for any user. No role-grant fixture, no instance initialization, no Registry/host bootstrap content. Application role fixtures, backend/frontend startup and browser tests remain for separate future scoped tasks and a Human Gate.
- Static verification (read-only): `ConvertFrom-Json` parse OK; redirectUris matches: 28000 callback ×1, 8000 ×0; wildcard characters ×0; `webOrigins: []` present; placeholder count 5 (`OIDC_CLIENT_SECRET`, `KC_SYNTHETIC_ADMIN1_PASSWORD`, `KC_SYNTHETIC_ADMIN2_PASSWORD`, `KC_SYNTHETIC_PM_PASSWORD`, `KC_SYNTHETIC_MEMBER_PASSWORD`); user count 4; literal (non-placeholder) password values ×0.

## Exact verification commands and results

1. `git status --porcelain=v1 -b` (session start and after writes) — exit 0. Pre-existing modifications/untracked preserved exactly; only the two allowlisted config files newly created under `dev/keycloak/`.
2. `docker compose --env-file .env.example -f dev/keycloak/compose.chpmis011-isolated.yaml --project-name chpmis023config --profile local-oidc config --quiet` — **NOT_VERIFIED (command did not run)**: `docker` is not recognized in this session's PATH (`CommandNotFoundException`); standard Docker install locations were not found (checked `LOCALAPPDATA\Programs\Docker\Docker\resources\bin`, `LOCALAPPDATA\Programs\Docker\resources\bin`, `Program Files\Docker\Docker\resources\bin`, `LOCALAPPDATA\Docker\bin`; a broader recursive scan timed out and was abandoned). Per the pack: Docker unavailable → record `NOT_VERIFIED` and stop without an alternate executable or permission change. No PATH change, no installation, no container/image action was attempted. Process-local synthetic literal placeholder values for `KC_SYNTHETIC_PM_PASSWORD`/`KC_SYNTHETIC_MEMBER_PASSWORD` were prepared and cleared immediately; they were never persisted, printed, or interpolated into any output.
3. `git diff --check` — **exit 0**. Output: 15 CRLF normalization warnings, all on pre-existing modified files (`.github/workflows/ci.yml`, `.team/ledger.md`, `.team/tasks/CHPMIS-011-*.md`, `ACCEPTANCE.md`, `OPEN_QUESTIONS.md`, `PLAN.md`, `README.md`, `TASKS.md`, and 4 `backend/` files) — none created by this Worker. **Zero** whitespace-error findings.
4. Untracked-file trailing-whitespace inspection (pack: `git diff --check` does not cover untracked files): read-only byte/regex scan of the two new files — 0 trailing-whitespace lines in both; LF-only line endings (CR=0). The Worker report file is also LF-only with no trailing whitespace. Limitation: this inspection is static, not `git diff --check` coverage.

## Assumptions and limitations (disclosed)

- **A1:** `chpmis023config` is used only as the fixed project name for config rendering, per the pack; it grants no authorization to create or reuse any project/service/volume.
- **A2:** Volume name `chpmis011_isolated_pgdata` is new and project-scoped; a source-wide scan found no existing reference to it. No host volume was inspected, created, or listed.
- **A3:** Ports 25432/28081 are fixed loopback values from the approved design; **port availability was NOT probed and is NOT claimed** (host/port probing is outside authorization).
- **A4:** The Compose config parse is **NOT_VERIFIED** in this session (Docker absent from PATH), so effective-config rendering (e.g., that the standalone file renders only the two loopback bindings and required env) is supported only by source inspection, not by a successful `config --quiet` run.
- **A5:** C/D department attribute values (`Administration`) are synthetic placeholders mirroring the reviewed realm's pattern; the pack does not fix them. No role/claim semantics are implied beyond the existing `department` mapper.
- **A6:** The prompts.chat MCP server was not exposed in this session's tool catalog (searched namespaces `prompts-chat`, `prompts_chat`, `prompts.chat`, `mcp`; MCP resource listing returned none), so the template could not be re-fetched live; it is cited from the pack and the prior verified retrieval (CHPMIS-011, 2026-10-31, ID `cmp1fv5ac0001js04jbj3pxoa`). No template content was invented.
- **A7:** `.env` was never read or modified; only `.env.example` was used, explicitly selected. No Registry/Registry-key, account, or ACL inspection of any kind was performed (the only "registry" scan was a filesystem search for a Docker executable). No login, no network/provider access, no browser action.
- **Not claimed:** live Keycloak/PostgreSQL, free ports, a live IdP, any migration, any role fixture or provider login, AC-05, AC-14, or any Human Gate approval. The candidate retains its later separate host/runtime Human Gate.

## DoD status

- Both files created satisfying the written contract (static inspection above); only allowlisted paths changed.
- `git diff --check` exit 0 with exact output disclosed; untracked-file trailing whitespace inspected and clean (static).
- Compose config parse: NOT_VERIFIED (Docker unavailable), recorded as a limitation, not a PASS.
- Independent OpenCode Reviewer approval: pending — this report requests it.

SUMMARY: Created loopback-only standalone Compose (25432/28081, new project volume, read-only four-user realm mount) and four-user non-secret realm variant with sole exact 28000 callback and placeholder-only credentials; diff check exit 0; Compose config parse NOT_VERIFIED (Docker absent from session PATH); no runtime, port, Registry, or host action taken.
ROLE_RESULT: review
