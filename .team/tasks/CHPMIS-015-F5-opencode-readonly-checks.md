# CHPMIS-015-F5 OpenCode Read-Only Checks

- **Task ID:** CHPMIS-015-F5-T1
- **Role:** OpenCode Tester (read-only)
- **Status:** NOT_VERIFIED — owner-authorized DeepSeek verifier run used `deepseek/deepseek-flash`, but the role's shell permission denied all six assigned checks before execution. Only an unassigned read-only `git status --short` ran (exit 0). No permission/configuration change or further retry is authorized by this pack.
- **Scope:** Independently verify the exact F5 commands in `.team/tasks/CHPMIS-015-F5-canonical-decision-authority.md`. Do not edit product files or clean up runtime/artifacts.
- **DoD:** Report exact command outputs/exits, skip status, and confirm the assigned tests exercise the two role-denial cases, canonical success, and bootstrap legacy detection.
- **Requirement trace:** `.team/tasks/CHPMIS-015-F5-canonical-decision-authority.md`, mission §4B.
- **Prompt template:** Not applicable; Tester task, no implementation work.
- **Earlier evidence:** Run `2026-11-01T15-51-06-verifier-chpmis-015-f5-read-only-verification-13c1`; session `ses_e683150e7ffe5lbkvuUe7D3oW4`; service `http://127.0.0.1:28894`; GUI visible; default route requested; cost USD 0; 274,516 input / 15,327 output tokens. Role result `blocked`, summary “Unable to run verification commands due to shell tool permission denial”; driver exit 0 means the verifier completed with a blocked role result, not that checks passed. No settings or permissions were changed.

## Exact owner authorization — 2026-11-02

Owner answered **“Approve DeepSeek verifier access”** to the request explaining that a CHPMIS-015-F5 OpenCode read-only retry would send repository code to the external `deepseek/deepseek-flash` model. This authorization is limited to this verifier pack, the parent F5 task pack, and the F5 diff in `backend/app/auth/routes.py` and `backend/tests/test_auth_remediation.py`. Run only the checks listed in `.team/tasks/CHPMIS-015-F5-canonical-decision-authority.md`, remain read-only, and do not change OpenCode/Hermes permissions or provider configuration. This does not authorize DeepSeek egress for F2 or any other task. Any provider/shell denial is `NOT_VERIFIED`; do not route around it.

## Authorized DeepSeek attempt — 2026-11-02

- OpenCode run `2026-11-02T01-17-36-verifier-chpmis-015-f5-authorized-deepseek-verifi-7780`; session `ses_e662aace7ffe7M6ni63Qu0NfHo`; role `role-verifier`; requested and used model `deepseek/deepseek-flash`; service `http://127.0.0.1:28894`; GUI visible; project path matches this repo.
- The verifier summary says all six assigned checks were rejected as `Permission denied: shell` before execution. An unassigned read-only `git status --short` ran with exit 0. Static inspection confirmed the four `legacy_role` tests and canonical-only decision filters; this is not runtime verification. Tests, Ruff, scoped diff check, and PostgreSQL skip behavior remain `NOT_VERIFIED` for this run.
- Agent run outcome was `blocked`, `role_result=blocked`, OpenCode process `exit_code=0`, wrapper exit code 1. `error_events` was empty and stderr tail empty. No OpenCode permissions, agent rules, or provider settings were changed; no second route/model was attempted.
- Metrics exposed in the board record: USD 0.010254756; 35,906 input / 3,170 output / 2,251 reasoning tokens; cache read 538,752. Duration 55.67 seconds. Resume form: `opencode run --session ses_e662aace7ffe7M6ni63Qu0NfHo -- "continue"`. Do not resume without new authorization and a changed shell-permission condition.
