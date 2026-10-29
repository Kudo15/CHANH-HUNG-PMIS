# Task Register

Tasks are the source list for execution order; detailed design lives in the plan and docs. No implementation task is dispatched until a real prompt template is located and required Human Gates are approved.

| Task ID | Role | Scope / trace | DoD and evidence | Status |
|---|---|---|---|---|
| CHPMIS-000 | Coordinator / Analyst / Architect | Audit and product/architecture/security/legal planning docs; PRD, roles, stories, architecture, model/API proposals, workflow, security, threat, legal register; traces to mission sections 1–7 | Required docs exist; proposals clearly distinguish confirmed requirements from open decisions; no product code changed; structural check exit 0 | COMPLETE |
| CHPMIS-001 | Human Gate + Security Reviewer | Decide identity/session, authorization matrix, project fields, task states/transitions, audit policy; `OPEN_QUESTIONS.md`, `SECURITY_MODEL.md`, `DATA_MODEL.md`, `WORKFLOW_CATALOG.md` | Written decisions and explicit approval recorded before schema/auth/workflow implementation | BLOCKED — decisions required |
| CHPMIS-002 | Worker + Reviewer | Frontend/backend/PostgreSQL/Compose/health/CI foundation (no identity/business schema); mission §2 and §7C | Local config validates; services bind to localhost; synthetic data only; health checks and automated test commands run; review verdict recorded | READY — plan confirmed and prompt templates verified; Docker runtime unavailable |
| CHPMIS-003 | Worker + Tester + Security Reviewer | Authentication and server-side RBAC/ABAC; mission §4 and §6 | Approved matrix enforced on all relevant API paths; positive and negative authorization tests pass; security review approved | BLOCKED — Human Gate |
| CHPMIS-004 | Worker + Tester + Reviewer | Projects, project staff assignment, tasks, approved task workflow; mission §3, §4 and §7D | Endpoints/UI meet acceptance IDs AC-05–AC-10; cross-scope and invalid-transition tests pass; audit events evidenced | BLOCKED — Human Gate |
| CHPMIS-005 | Worker + Tester + Reviewer | Scoped dashboard, audit view, E2E vertical slice; mission §7D and §8 | AC-11–AC-15 evidenced in automated tests; local walkthrough recorded; no unauthorized aggregate leakage | BLOCKED — CHPMIS-001–004 |
| CHPMIS-006 | Tester + Independent Reviewer | Full regression, security review, final report; mission §5, §6, §8 | Exact commands/results, review verdict, risks and next priorities recorded; PASS only for criteria with evidence | BLOCKED — implementation tasks |

## Dispatch controls
- Required prompt template for worker tasks: `NEEDS_HUMAN_SELECTION` until prompt-lookup/prompt-librarian is installed and verified.
- No task is allowed to change stack, deploy, use real agency data, or bypass a Human Gate.
- Update `.team/ledger.md` for every task with harness/model/provider/profile/effort only when observed; otherwise use `NEEDS_HUMAN_SELECTION`.
