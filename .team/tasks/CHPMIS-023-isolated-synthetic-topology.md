# CHPMIS-023 — Prepare isolated synthetic identity topology

## Identity and authority

- **Role:** OpenCode Worker → independent read-only OpenCode Reviewer; **trace:** CHPMIS-011/012-F2, AC-05/14, mission §5–6.
- **Status:** COMPLETE — bounded synthetic configuration preparation and independent static review complete. Compose config parsing remains NOT_VERIFIED; no provider login or host/runtime action is authorized.
- **Required session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this pack, `.team/tasks/CHPMIS-011-local-oidc-bootstrap.md`, `.team/tasks/CHPMIS-011-runtime-approval-proposal.md`, `.team/tasks/CHPMIS-011-runtime-candidate-r2-review.md`, `docs/MISSION.md`, `ACCEPTANCE.md`, and the current `compose.yaml`/`dev/keycloak/realm.json`. Run `git status --short` before edits; preserve all prior work.
- **Prompt template:** prompts.chat **Feature coding template**, Onyekachi Ibekwe, ID `cmp1fv5ac0001js04jbj3pxoa`, previously located/retrieved using installed `prompt-lookup` and cited in CHPMIS-011. Adaptation: “As a bounded synthetic configuration Worker, prepare two isolated, loopback-only Compose/realm files with no real credentials, check only the assigned configuration commands, disclose all limitations and request independent review. Do not start services, change auth behavior, commit, or edit files outside the allowlist.”

## Objective and exact write scope

Create only:

1. `dev/keycloak/compose.chpmis011-isolated.yaml` — a standalone synthetic test Compose definition for **only** a new PostgreSQL service and a Keycloak service, with a project-scoped named volume. It must not inherit the root Compose `ports` lists or control existing projects/services.
2. `dev/keycloak/realm.chpmis011-isolated.json` — a non-secret four-user synthetic realm variant based on the current reviewed realm, for initial admins A/B, separate PM C and separate Member D. No role-grant fixture is implemented here.
3. `.team/tasks/CHPMIS-023-worker-report.md` — append-only evidence and handoff.

Do not edit root `compose.yaml`, `.env.example`, the existing realm, product/test code, dependency files, CI, runbooks, Registry, accounts, credentials or any other path. Do not make temp scripts/files. Do not read or modify an existing `.env`. No container/image start/stop/build/pull, volume/database/Registry/account/ACL action, provider/network login, stage/commit/push/deploy, permission changes or subagents. Stop BLOCKED if these constraints prevent a safe design.

## Configuration contract

- PostgreSQL image matches existing `postgres:17-bookworm`; bind host `127.0.0.1:25432` only; data in a new **project-scoped** named volume, never an external or existing volume. Preserve existing synthetic DB/user/password interpolation names and require a process-supplied password. Keycloak image matches existing `quay.io/keycloak/keycloak:26.8.1`; bind host `127.0.0.1:28081` only; set `KC_HOSTNAME=http://127.0.0.1:28081`, retain current reviewed import/hostname/backchannel behavior, and mount the new realm file read-only. Do not publish backend/frontend ports or start those services in this standalone file.
- New realm uses exactly `http://127.0.0.1:28000/api/v1/auth/callback` as its sole client redirect URI; no wildcard or broad web origins. Preserve the current reviewed client/auth protocol semantics. A/B are the existing synthetic admin identities; add distinct synthetic C/D named clearly as project-manager/member test users. C/D passwords use distinct process-supplied `${KC_SYNTHETIC_PM_PASSWORD}` / `${KC_SYNTHETIC_MEMBER_PASSWORD}` placeholders; A/B and OIDC secret remain environment placeholders, never literal credentials. No real user/agency records.
- No static identity receives a global application role in the realm file; application role fixtures, instance initialization, host bootstrap/Registry provisioning, backend/frontend startup and browser tests belong to separate future scoped tasks and Human Gate. Do not claim a role fixture or provider login exists.
- The final runtime will use a unique project selected at execution and must stop if it or the planned volume/ports already exist. The fixed project name used below is for **config rendering only**, not authorization to create or reuse a service.

## Exact allowed verification

From repository root, with the existing `.env.example` explicitly selected and **only** synthetic literal placeholder values supplied process-locally for `KC_SYNTHETIC_PM_PASSWORD` and `KC_SYNTHETIC_MEMBER_PASSWORD`:

1. `docker compose --env-file .env.example -f dev/keycloak/compose.chpmis011-isolated.yaml --project-name chpmis023config --profile local-oidc config --quiet` — config parsing only; no `up`, build, pull or connection to a provider. Record exact exit/output; never print interpolated credentials. If Docker/Compose is unavailable or denies execution, record `NOT_VERIFIED` and stop without an alternate executable or permission change.
2. `git diff --check` — exit/output. New untracked files are not covered; additionally inspect them for trailing whitespace and report the limitation without modifying other files.

Independently inspect the two configuration files themselves for exact ports, read-only realm mount, four synthetic users, exact single redirect and no literal credentials; this is source inspection, not runtime proof. Report exact file scope, any assumptions, commands/exits, and whether the config command actually ran. Do not claim actual port availability, a live IdP, PostgreSQL, authenticated browser, AC-05/14, or host gate approval.

## Definition of Done

Both files satisfy this contract, only allowed paths changed, exact configuration/whitespace evidence is reported, and an independent OpenCode Reviewer approves the changes. The candidate retains its later separate host/runtime Human Gate and existing resources remain untouched.

## Independent Reviewer result — 2026-11-05

- CHPMIS-023-R1 OpenCode Reviewer: **APPROVED** for the static configuration scope; 0 P1/P2 and 2 P3 report-completeness notes. No edits or runtime commands were made by the Reviewer.
- Run `2026-11-05T02-50-54-reviewer-chpmis-023-independent-config-review-7b72`; session `ses_e56622afdffeHxGiJh9zbo5a5M`; driver exit 0, outcome `succeeded`, `gui_visible=true`, service `http://127.0.0.1:28894`. Reviewer final output reported `auto:coding` / `openai-completions`; driver metadata did not expose a model ID and reported cost `$0`; profile/effort not exposed.
- Findings: `.team/tasks/CHPMIS-023-worker-report.md:47` omits two modified files from its CRLF-warning filename list (P3); line 18's byte-identical preservation statement lacks recorded per-file hashes (P3). Neither blocks the static task closure; retain as reporting/process notes.
- Docker Compose config parsing remains **NOT_VERIFIED** because Docker was unavailable in the Worker session and no alternate executable was attempted. This is not runtime evidence and does not change AC-05 or AC-14.
- The earlier `TASKS.md` statement that the Worker prompt remained unsent is superseded by the Worker report and this review. The separately gated CHPMIS-011 host/runtime procedure remains open.

SUMMARY: Worker prepared the synthetic isolated topology; static contract independently APPROVED (0 P1/P2, 2 P3); Compose config parse NOT_VERIFIED; no runtime or AC-05/14 claim.
ROLE_RESULT: done
