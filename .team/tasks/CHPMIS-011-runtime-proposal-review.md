# CHPMIS-011 — Independent runtime proposal security review

- **Task ID:** CHPMIS-011-RUNTIME-R1; **role:** independent OpenCode read-only security-focused Reviewer; **trace:** AC-05/AC-14, CHPMIS-011 and CHPMIS-016.
- **Session start:** Read `AGENTS.md`, `.team/CHARTER.md`, `.team/ledger.md`, this task pack, `docs/MISSION.md`, and `ACCEPTANCE.md` before review; report the required reads.
- **Objective:** Review `.team/tasks/CHPMIS-011-runtime-approval-proposal.md` against current product code, `compose.yaml`, the existing DO NOT EXECUTE runbook, and the CHPMIS-011/016 task packs. Identify specific prerequisites and evidence needed before a safe, separately approved local synthetic runtime and bootstrap procedure could be implemented.
- **Boundaries:** Read only. No product, documentation, configuration or credential edits; no Registry/account/ACL inspection, network provider, Docker, PostgreSQL, test execution or host changes. Do not assume two synthetic keys prove two people. Do not authorize or run the existing runbook. No other agents.
- **Review criteria:** Check the fixed Registry trust path/values/security descriptor and actual CLI input against code and task evidence; flag stale runbook assumptions, blocked ports and unsupported steps; assess what must be specified about isolated runtime, secure synthetic credentials, existing-object conflicts, process token/ACL verification, evidence and preservation. Identify what is needed to create an authenticated E2E test without claiming the shell smoke test covers it.
- **DoD:** Return `APPROVED FOR PLANNING` or `CHANGES_REQUESTED`, concrete findings with file/line when possible, and a minimal ordered list of what the exact procedure must establish. State clearly that no host action or provider login has been approved or performed and that Human Gate remains. Do not claim execution evidence.

SUMMARY: <one line>
ROLE_RESULT: <done|review|blocked>

## Initial run — 2026-11-03

OpenCode run `2026-11-03T04-51-58-reviewer-chpmis-011-synthetic-runtime-proposal-se-4a21`, session `ses_e60400d87ffe3tJ0XXdq8vLMXQ`, timed out after 600 seconds; driver exit 1 / SIGTERM, no role result or verdict. GUI listing was confirmed. Model not exposed, cost 0, tokens in 195923 / out 1546 / cache-read 243200. The role's last recorded summary was that it was reading product code. This is NOT_VERIFIED and does not approve a host procedure or establish that all session-start requirements were met.

The GUI session's updated timestamp later advanced to 12:08:37 Bangkok after the driver timeout. The session may still be running on the shared OpenCode service; no duplicate or resumed session was launched.

## Post-timeout result and Coordinator assessment

The same session completed at `2026-11-03T05:30:51.679Z` with `ROLE_RESULT: review` / **CHANGES_REQUESTED**: two P1, six P2 and three P3 findings. Exported final-message model `auto:coding`, provider `openai-completions`, cost 0; final-message tokens in 24610 / out 4233 / cache-read 72000 (not a session total). The driver timeout/exit 1 remains historical; no duplicate or resume was launched. The transcript shows a charter read, but full mission/ledger/acceptance session-start reads are not established, so this is advisory evidence, not the independent approval required for a host-change runbook.

- **P1 F1:** instance state is lazily created during bootstrap but the signed payload must already match it. Coordinator confirmed `get_or_create_instance_state()` creates/commits the UUID and the CLI validates the supplied value against it. The safe conclusion is that a fresh database needs a reviewed pre-initialization/read step before signing; the categorical claim that bootstrap can never succeed is too broad because the helper can be invoked before the CLI. No runtime action was performed.
- **P1 F2; P2 F3/F4:** runbook CLI, payload, expiry/instance binding, PKCE/browser-cookie and migration-head details are stale. Coordinator confirmed stdin ingestion and the expanded signed payload in current code. A replacement procedure must be reviewed; the existing runbook remains DO NOT EXECUTE.
- **P2 F5/F6:** enumerate actual planned port bindings and existing preserved projects/volumes/Registry namespace; resolve conflicts without changing them. The reviewer suggests process-only Compose credentials as a candidate. Its list of ports is a snapshot and omits later dynamically assigned task ports; occupancy of an unrelated port should not automatically block a plan that does not bind it.
- **P2 F7:** reviewer reports the signed `environment` is not compared to an authoritative runtime environment. Coordinator confirmed the shown bootstrap path takes the value from the payload; impact and any policy/code correction require separate security analysis and a Human Gate, not a runtime assumption.
- **P2 F8:** current frontend lacks a login UI and callback returns JSON. This is a real usability/E2E design gap; whether AC-14 necessarily requires a product change rather than an explicitly navigated browser test remains unverified. Do not assume either approach is approved.
- **P3 F9–F11:** document the exact protected Registry descriptors, access checks, UTC validity and signed operator claim. The reviewer suggests a standard account and says an admin-run CLI always fails; actual token rights and Windows UAC filtering must be verified before treating that as an unconditional fact.

All findings are inputs for a new concrete procedure and compliant independent review. They do not authorize Registry/account/ACL changes, service startup, credential use, provider login, or product edits.
