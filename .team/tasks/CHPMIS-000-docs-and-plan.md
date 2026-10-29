# Task Pack — CHPMIS-000

## Task ID and execution role
- Task ID: CHPMIS-000
- Owner/role: Current Coordinator (with Analyst/Architect responsibilities)
- Status: COMPLETE

## Context and objective
Repository initially contained only bootstrap files and no application. Translate the user's master mission into traceable product, architecture, security, legal-register, acceptance, and execution-planning documents without implementing product code or inventing real organizational/legal policy.

## Files in scope
- Update: `AGENTS.md`, `README.md`, `PLAN.md`, `.team/CHARTER.md`, `.team/TASK-PACK.md`, `.team/ledger.md`, `docs/MISSION.md`.
- Create: `TASKS.md`, `ACCEPTANCE.md`, `OPEN_QUESTIONS.md`, requested files under `docs/product/`, `docs/architecture/`, `docs/workflows/`, `docs/security/`, `docs/legal/`, and the vertical slice plan under `docs/superpowers/plans/`.
- Forbidden: all product-code paths, dependencies, schema/migrations, provider configs, real data, Git commit/push/deploy.

## Traceability
Master mission §§1–8; first vertical slice; security and Human Gate rules.

## Acceptance / DoD
- [x] All requested documents exist and cross-reference each other.
- [x] Unspecified organizational, identity, legal, workflow, and financial rules are explicitly TBD/proposed/open.
- [x] Scope is limited to the first vertical slice; deferred modules are identified.
- [x] No product code, migrations, dependencies, or deployment artifacts were added.
- [x] Structural check passed; routing JSON parsed.

## Verification command and evidence
- Command: PowerShell structural assertions over 27 required paths, required mission headings, `.team/routing.json` parse, and absence of `frontend/`, `backend/`, `compose.yaml`.
- Result: `PASS: 27 required paths exist; mission headings and routing JSON verified; no product scaffold present.` Exit code `0`.
- Test evidence: documentation structural check only; no product test commands exist yet.

## Prompt template
- `NOT_APPLICABLE` — coordinator-authored planning/documentation; no Worker was dispatched.

## Risks / boundaries
This work is a proposal pending plan review and Human Gates. It does not approve auth/session, data schema, role matrix, workflow transitions, audit retention, legal rules, or deployment.

## Report format
Files, structural check result/exit code, unresolved Human Gates.
