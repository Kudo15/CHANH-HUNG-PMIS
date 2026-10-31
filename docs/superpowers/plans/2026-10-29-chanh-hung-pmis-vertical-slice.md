# CHÁNH HƯNG PMIS Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a secure local first slice: sign in → create project → assign staff → create/assign/update task → view scoped dashboard → inspect audit history.

**Architecture:** Modular monolith with a React/Vite frontend and FastAPI backend over a PostgreSQL database. Backend owns authentication, RBAC/ABAC checks, workflow validation, and audit writes; local services run through Docker Compose bound to localhost.

**Tech Stack:** React + TypeScript + Vite + Tailwind + shadcn/ui; FastAPI + SQLAlchemy 2 + Alembic + Pydantic; PostgreSQL; Docker Compose; Pytest + Vitest + Playwright; CI. S3-compatible storage is deferred until document storage enters scope.

**Spec:** `docs/MISSION.md`, `docs/product/PRD.md`, `docs/product/USER_STORIES.md`, `docs/architecture/ARCHITECTURE.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/API_CONTRACT.md`, `docs/workflows/WORKFLOW_CATALOG.md`, `docs/security/SECURITY_MODEL.md`, `docs/security/THREAT_MODEL.md`, `ACCEPTANCE.md`, `OPEN_QUESTIONS.md`.

## Global Constraints
- Use the exact mandated stack and modular-monolith architecture unless an ADR is approved.
- MVP modules are M01–M06 and M15; this plan implements only the specified first slice.
- No real agency data in development; no secrets or sensitive documents in Git.
- Local services bind to `127.0.0.1`; no production deploy, push, merge, or remote creation.
- Backend enforces role, department, project, workflow-state, and document-restriction authorization.
- Do not hardcode departments, titles, or approval routes. Keep internal approval distinct from statutory/legal approval.
- Human Gate is required before schema, auth/session, authorization, task workflow, audit policy, financial logic, provider integration, or deployment implementation.
- Worker tasks require a real prompt template found through the installed prompt-search skill; until then tasks remain undispatched.
- No task is PASS without real command output, exit code, and traceable evidence.

## Review Focus
- Cross-project identifier guessing must not disclose data → test ownership/scope on project item reads and task endpoints in Task 4.
- Cross-department list/dashboard aggregation must not leak record existence/counts → test filtered collections and aggregates in Task 5.
- Invalid/current-state transitions and unauthorized actors must be rejected → test both in Task 4 after workflow Human Gate.
- Authentication/session expiry or inactive account must deny protected access → test in Task 3 after identity Human Gate.
- Failed writes and audit failures must not silently claim success or omit required history → test transaction/audit behavior in Task 5 after audit policy approval.

---

## Planned File Structure

- `frontend/` — Vite app, UI, API client, Vitest and Playwright tests.
- `backend/app/` — FastAPI application, settings, API routes, service/domain modules, authorization, persistence, audit.
- `backend/alembic/` — migration environment and approved schema revisions.
- `backend/tests/` — unit, API integration, auth and authorization tests.
- `compose.yaml` — local web/API/PostgreSQL services with loopback-only published ports.
- `.github/workflows/ci.yml` — checks and test jobs only; no deployment.
- `README.md`, `.env.example` — synthetic local setup and variable names only.

## Task 1: Foundation Scaffold

**Role:** Worker; independent Reviewer.
**Prompt templates (retrieved from prompts.chat):** `System Architect Agent Role` (template ID `cmmx2hvgz0001ks04mcg6dizn`) and `Test Engineer Agent Role` (template ID `cmmx34zl7000vil04rm2wl8yl`); modernize them to this bounded scaffold and fixed stack, omit microservices/cloud-scale defaults, and honor this plan's local-only and no-business-schema limits. Reviewer uses `Senior Code Reviewer (severity-ranked)` (template ID `cmv9n79m30005ku060pzornri`), adapted to the charter's spec-first review and P1/P2/P3 findings.
**Files:** create the planned `frontend/`, `backend/`, `compose.yaml`, `.github/workflows/ci.yml`; modify `README.md`, `.env.example`, `.gitignore` only as required.
**Interfaces:** expose backend liveness/readiness; frontend build/test scripts; backend pytest/lint scripts; PostgreSQL readiness; no product-auth or business schema in this task.

- [x] Write `backend/tests/test_health.py::test_live_returns_ok`, `test_ready_reflects_database_availability`, and `frontend/src/App.test.tsx::renders_application_shell`.
- [x] Run focused backend/frontend tests first and record the expected initial failures (both observed).
- [x] Implement pinned dependencies and scripts; add Docker Compose with all host ports on `127.0.0.1`, a health-checked PostgreSQL service, and no real data/secrets.
- [x] Add `/health/live` and `/health/ready`; readiness reports dependency failure accurately.
- [x] Add CI for config validation, backend/frontend checks and tests; no deployment steps.
- [x] Run available backend/frontend tests, lint, build, E2E, and offline migration checks; exact results are in `ACCEPTANCE.md`. `docker compose config` could not run because Docker is absent and remains `NOT_VERIFIED`.
- [x] Independent Reviewer reviewed localhost bindings, secrets, dependencies, health semantics, and scope; verdict `APPROVED`.

**Execution result:** Partial. Local checks pass and the independent reviewer approved. Compose configuration/runtime, migration against PostgreSQL, and remote CI have not been verified. See `ACCEPTANCE.md` and `.team/ledger.md`.

**DoD:** repeatable local foundation with valid Compose, health checks, actual test commands, CI tests, synthetic-only configuration, and independent review.
**Gate:** no schema/auth implementation in this task. Prompt template and human plan review must be complete before dispatch.

## Task 2: Approve Identity, Schema, Authorization, Workflow, and Audit Decisions

**Role:** Human Gate owner with Architect and Security Reviewer; no worker implementation.
**Files:** review/update `OPEN_QUESTIONS.md`, `docs/product/USER_ROLES.md`, `docs/architecture/DATA_MODEL.md`, `docs/architecture/API_CONTRACT.md`, `docs/workflows/WORKFLOW_CATALOG.md`, `docs/security/SECURITY_MODEL.md`.

- [ ] Choose identity source/session mechanism and account lifecycle.
- [ ] Approve first-slice project fields and department/project scope model.
- [ ] Approve task states/transitions/actors and internal-vs-legal boundary.
- [ ] Approve audit fields, protected readers, denied-attempt policy, and retention.
- [ ] Record explicit Human Gate decisions and update the corresponding docs.

**DoD:** no security-sensitive implementation starts until each decision is explicit and recorded. This task cannot be inferred from tests.

## Task 3: Authentication and Authorization Foundation

**Role:** Worker; Security Reviewer independent; Tester supplies evidence.
**Prompt templates:** System Architect Agent Role + Test Engineer Agent Role; Reviewer: Senior Code Reviewer (severity-ranked), all modernized to the approved identity/policy decisions and the no-real-data boundary.
**Files:** `backend/app/auth/`, `backend/app/authorization/`, identity-related approved migration(s), tests in `backend/tests/`, frontend sign-in/API-session surfaces.
**Interfaces:** API requests resolve an authenticated principal; policy checks receive principal + action + resource context; exact types/fields must match approved Task 2 decisions.

- [ ] Write tests for anonymous, inactive, valid identity, and session expiry/revocation as approved.
- [ ] Run targeted tests to establish failures.
- [ ] Implement approved authentication and reusable deny-by-default authorization dependencies.
- [ ] Add tests for role permission, department boundary, project assignment scope, and object ID guessing.
- [ ] Run `pytest -q backend/tests/auth backend/tests/authorization` and frontend auth tests; record exit codes.
- [ ] Security Reviewer verifies every relevant API route uses server-side checks and returns non-disclosing failures.

**DoD:** all approved identity and policy cases pass; no client-provided role/scope is trusted; independent security verdict recorded.
**Gate:** Task 2 approval required before schema or code.

## Task 4: Project, Assignment, Task, and Workflow Slice

**Role:** Worker; Tester; independent Reviewer.
**Prompt templates:** System Architect Agent Role + Test Engineer Agent Role; Reviewer: Senior Code Reviewer (severity-ranked), scoped to the approved project/task contracts.
**Files:** approved project/task domain modules, migrations, API routes/schemas, frontend project/task flows, focused tests.
**Interfaces:** project CRUD and project assignment use Task 3 principal/policy; task status mutation calls the approved transition policy. Task 4 also owns the approved audit-write interface, `AuditEventWriter.write(actor, action, target, safe_context, correlation_id)`, used by its project/assignment/task mutations. Task 5 consumes this writer/storage to expose the authorized read path.

- [ ] Write tests for approved project fields, create/read/list permissions, assignment, task creation/assignment, valid and invalid state changes.
- [ ] Run targeted tests and record failures.
- [ ] Implement minimal transactional services/endpoints and UI required by US-010/011/020/021.
- [ ] Add cross-project and cross-department negative cases, including guessed IDs and list filters.
- [ ] Run targeted backend/frontend tests and migration checks; record exit codes.
- [ ] Reviewer validates requirement trace, configurable organization/workflow values, and no statutory approval semantics.

**DoD:** approved project/staff/task journey works and positive/negative criteria have evidence.
**Gate:** Tasks 2 and 3 approved.

## Task 5: Scoped Dashboard and Audit History

**Role:** Worker; Tester; Security Reviewer and Reviewer independent.
**Prompt templates:** System Architect Agent Role + Test Engineer Agent Role; Reviewer: Senior Code Reviewer (severity-ranked), modernized to focus on scope leakage and audit policy.
**Files:** dashboard/audit read services and API/UI, audit persistence from approved schema, authorization and integration tests.
**Interfaces:** dashboard consumes policy-filtered project/task query; audit read uses Task 4's `AuditEventWriter` persistence contract; audit read API enforces approved reader permissions.

- [ ] Write tests for scoped counts/lists, audit event fields, unauthorized audit reads, and required history on project/assignment/task transitions.
- [ ] Run targeted tests to establish failures.
- [ ] Implement minimal summary view and audit-history view; avoid sensitive payloads.
- [ ] Test atomicity/behavior when audit persistence fails according to approved policy.
- [ ] Run targeted backend/frontend tests; record exit codes.
- [ ] Security Reviewer checks for aggregate leakage, audit integrity/access, and sensitive logging.

**DoD:** AC-11–AC-13 evidence exists; independent security and quality verdicts recorded.
**Gate:** Task 2 audit/scope approval.

## Task 6: End-to-End Verification and Release Readiness (Local Only)

**Role:** Tester/QA; independent Reviewer; Security Reviewer.
**Prompt templates:** Test Engineer Agent Role; Reviewer: Senior Code Reviewer (severity-ranked), adapted to full acceptance/security evidence and charter verdicts.
**Files:** Playwright tests, acceptance evidence, task ledger/report; fix implementation only through a new scoped Worker task.

- [ ] Add Playwright path for sign in → project → staff assignment → task state → dashboard → audit.
- [ ] Run Compose, migrations, backend/frontend suites, E2E suite, and configured static checks; record exact commands and exit codes.
- [ ] Review each AC-01–AC-15 individually; mark unmet/missing evidence `NOT_VERIFIED` or `BLOCKED`.
- [ ] Security Reviewer checks threat-model controls against actual code/config/tests.
- [ ] Reviewer performs spec-first then quality/safety review and records `APPROVED` or `CHANGES_REQUESTED` with file:line findings.
- [ ] Produce final report with working features, incomplete features, risks, Human Gates, and prioritized next tasks.

**DoD:** report is evidence-backed; local release readiness is not represented as production approval.

## Self-Review / Known Gaps
- Covers all first-slice steps and MVP platform requirements in mission §7C–E; deferred modules are explicitly excluded.
- Exact auth fields, role matrix, project fields, task states, audit rules, toolchain versions, and CI provider remain unresolved by design and are Human Gates, not implementation guesses.
- Current repository has no application files or test commands; Task 1 must create them before later commands become executable.
- No legal rules are included; Legal Verifier work begins only for a scoped later module and uses authoritative sources.
