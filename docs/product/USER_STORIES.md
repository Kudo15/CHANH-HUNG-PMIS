# User Stories

Stories are MVP candidates based only on the master mission. Personas are generic; authorization details require Human Gate approval.

## Authentication
- **US-001:** As an authorized staff member, I can sign in to use functions granted to my account.
- **US-002:** An unauthorized or inactive user cannot access protected data or actions.

## Projects and assignments
- **US-010:** As a permitted user, I can create a project with approved minimum fields and see it in my authorized project list.
- **US-011:** As a permitted project manager, I can assign an authorized staff member to a project.
- **US-012:** A user without project scope cannot read or change the project, including by guessing its identifier.

## Tasks and workflow
- **US-020:** As an authorized project participant, I can create a task for an authorized project and assign a responsible staff member.
- **US-021:** As an authorized user, I can change task state only along an approved transition.
- **US-022:** A user cannot update tasks outside their project/department scope or bypass a workflow rule.

## Dashboard and audit
- **US-030:** I can see project/task summaries only for projects I may view.
- **US-031:** An authorized auditor/administrator can inspect actor, action, target, and time for important project/task changes.
- **US-032:** Dashboard results reveal neither counts nor existence of unauthorized records.

## Deferred scope
Document upload, notifications, procurement, contracts, progress, cost, capital/disbursement, settlement, reports, AI, and integrations need separate acceptance criteria. No statutory approval route is inferred.

## Open decisions
Project required fields; dashboard indicators; task states; assignment/delegation; audit visibility and retention. See `../../OPEN_QUESTIONS.md`.
