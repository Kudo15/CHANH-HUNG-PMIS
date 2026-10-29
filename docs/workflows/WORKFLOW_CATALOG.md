# Workflow Catalog

> No official approval route or legal process is defined. Internal task workflow is distinct from statutory/legal approval.

## First-slice candidate
A task needs configurable state and permitted transitions. Illustrative states might be `open`, `in_progress`, `blocked`, `done`; these values and transition rights are **not approved**. Do not implement until the owner confirms meanings, reopening/cancellation, assignment, and who may transition each state.

## Required properties
- States and transitions are configurable, not hardcoded to department names/titles.
- Backend transition checks include role, department/project scope, and current state.
- Important transitions create audit history with actor and time.
- Internal coordination/review does not imply legal approval.
- Workflow-definition administration is controlled and audited.

## Deferred catalogs
Project lifecycle, document review, procurement, contract, progress, finance, disbursement, acceptance, settlement, and statutory approval need separate discovery and authoritative legal verification where applicable. No route, SLA, delegated authority, or automatic approval is asserted.
