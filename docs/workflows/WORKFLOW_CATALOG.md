# Workflow Catalog

> First-slice task workflow was approved by the project owner on 2026-10-30 for local development. No official approval route or legal process is defined. Internal task workflow is distinct from statutory/legal approval.

## Approved first-slice task states and transitions
- States: `open`, `in_progress`, `blocked`, `done`, `cancelled`.
- Ordinary work path: `open → in_progress`; `in_progress → blocked|done`; `blocked → in_progress`.
- Project Manager may cancel an unfinished task and reopen `done → in_progress`; `cancelled` is terminal.
- Member may transition only a task assigned to them along the ordinary work path. Project Manager may assign/reassign only within the explicitly scoped project and may perform the management transitions above.
- Project Manager may archive an in-scope project. Archived projects are read-only; no delete transition is approved.
- These internal coordination states do not represent statutory/legal approval, acceptance, or other legal authority.

## Required properties
- States and transitions are enforced by the backend; role names are policy keys, not department names/titles.
- Backend transition checks include role, department/project scope, and current state.
- Important transitions create audit history with actor and time.
- Internal coordination/review does not imply legal approval.
- Workflow-definition administration is controlled and audited.

## Deferred catalogs
Project lifecycle, document review, procurement, contract, progress, finance, disbursement, acceptance, settlement, and statutory approval need separate discovery and authoritative legal verification where applicable. No route, SLA, delegated authority, or automatic approval is asserted.
