# Task Ledger

Single source of truth for task routing, verification, review outcomes, and Human Gates. Record only observed harness/model/provider/profile/effort. Use `NEEDS_HUMAN_SELECTION`, `NOT_VERIFIED`, or `NOT_APPLICABLE` rather than guessing.

| Task ID | role | prompt template | harness | model | provider | profile | effort | verify | review verdict | ruling |
|---|---|---|---|---|---|---|---|---|---|---|
| CHPMIS-000 | Coordinator / Analyst / Architect | NOT_APPLICABLE — coordinator documentation | Codex desktop | NOT_EXPOSED | NOT_EXPOSED | NOT_APPLICABLE | NOT_EXPOSED | PowerShell structural assertions: 27 paths/headings/routing/no product scaffold; exit 0 | NOT_RUN | COMPLETE — planning docs created; no product code |
| CHPMIS-001 | Human Gate owner + Architect + Security Reviewer | NOT_APPLICABLE — human decision | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | Human decision record required | NOT_RUN | BLOCKED — plan review/policy decisions |
| CHPMIS-002 | Worker + Reviewer | System Architect Agent Role (cmmx2hvgz0001ks04mcg6dizn) + Test Engineer Agent Role (cmmx34zl7000vil04rm2wl8yl), modernized in task pack | Codex subagent (planned) | gpt-6.1-sol (planned) | OpenAI/Codex (planned) | NOT_APPLICABLE | medium | Planned Compose/tests/CI; commands not yet present; Docker unavailable | NOT_RUN | READY — plan confirmed and prompt templates verified; no identity/business schema |
| CHPMIS-003 | Worker + Tester + Security Reviewer | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | Planned auth/authorization tests; commands not yet present | NOT_RUN | BLOCKED — Human Gate and prompt template |
| CHPMIS-004 | Worker + Tester + Reviewer | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | Planned project/task/workflow tests; commands not yet present | NOT_RUN | BLOCKED — Human Gate and prompt template |
| CHPMIS-005 | Worker + Tester + Security Reviewer + Reviewer | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | Planned dashboard/audit tests; commands not yet present | NOT_RUN | BLOCKED — prerequisites and prompt template |
| CHPMIS-006 | Tester + Independent Reviewer | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | NEEDS_HUMAN_SELECTION | Planned full regression/security/E2E | NOT_RUN | BLOCKED — implementation tasks |

## SDD Preflight — Vertical Slice Plan

| Tasks / self-check | Shared files or interface | Scan result | Ruling |
|---|---|---|---|
| Task 1 ↔ Task 3 | Frontend shell and backend app foundations consumed by sign-in/auth surfaces | Foundation output is generic shell/health only; Task 3 adds auth after Human Gate; no auth policy is embedded in Task 1 | Proceed; keep Task 1 free of auth/business schema |
| Task 3 ↔ Task 4 | Principal and deny-by-default policy consumed by project/task routes | Task 3 produces authenticated principal + authorization dependency; Task 4 consumes them using Task 2 approvals | Proceed; approval matrix remains a prerequisite |
| Task 4 ↔ Task 5 | Audit write/read | Initial wording made Task 4 depend on a later Task 5 interface; corrected: Task 4 owns `AuditEventWriter.write(actor, action, target, safe_context, correlation_id)`, Task 5 consumes it for reads | Proceed with corrected interface |
| Task 2 ↔ Tasks 3–5 | Approved identity, scope, workflow, audit decisions | Human decisions are explicit inputs; no tests substitute for approval | Do not dispatch dependent tasks until recorded |
| Task 1 self-consistency | Compose, health, migrations, tests, CI | Empty baseline migration only; no product/auth tables; Docker is absent so Compose checks may be `NOT_VERIFIED`; Task 1 DoD and task pack say so | Proceed; do not install Docker or claim Compose validation |
| Task 2 self-consistency | Open policy items / evidence | Approval record, not code/tests, is the evidence | Proceed as a Human Gate, not a Worker task |
| Task 3 self-consistency | Auth and authorization tests/files | Tests cover approved identity/scope; implementation depends on Task 2 | Proceed only after gate |
| Task 4 self-consistency | Project/task schema, routes, transitions, audit writes | Tests and files align with approved fields and `AuditEventWriter`; no legal approval state is inferred | Proceed only after gate |
| Task 5 self-consistency | Scoped dashboard and audit read | Reads consume Task 4 persisted audit contract and approved access policy | Proceed only after Task 4 and audit gate |
| Task 6 self-consistency | E2E, security and final review | Uses acceptance IDs and actual test commands created by earlier tasks | Proceed after implementation; missing evidence stays `NOT_VERIFIED` |
