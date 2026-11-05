# CHPMIS-018-F1-T1-DIAG1 — OpenCode Environment Propagation

- **Task ID:** CHPMIS-018-F1-T1-DIAG1
- **Role:** OpenCode read-only verifier (`role-verifier`)
- **Status:** DONE — one permitted diagnostic command returned `PRESENT`, exit 0. This is not PostgreSQL test evidence.
- **Trace:** CHPMIS-018-F1-T1 retry environment prerequisite; this diagnostic does not verify the PostgreSQL reproduction.

## Objective and scope

Determine whether the OpenCode verifier's shell receives the harmless `CHPMIS_T1_ENV_SENTINEL` marker supplied only to the dispatch process. The marker is synthetic and is not a credential. Do not inspect or print any other environment variable, connection string, credential, or configuration value. Do not edit files, start services, access databases, run tests, or run any command besides the one below.

## Sole assigned command

From the project root, in one shell tool call:

`python -c "print('PRESENT' if __import__('os').environ.get('CHPMIS_T1_ENV_SENTINEL') else 'ABSENT')"`

Report the exact output and process exit code. If the command is denied or Python cannot be launched, report `BLOCKED` with the exact denial or error; do not retry through a wrapper, another interpreter, or a modified permission rule.

## Definition of Done

- The role reports whether the marker was `PRESENT`, `ABSENT`, or the command was blocked, with exact output and exit code when available.
- The role changes no file and makes no database or service call. It does not claim T1 verification.
- Finish with the standard `SUMMARY` and `ROLE_RESULT` lines; the Coordinator records the result in `.team/ledger.md`.

## Result

- OpenCode run `2026-11-03T03-58-38-verifier-chpmis-018-f1-t1-opencode-environment-di-8e11`, session `ses_e6070df5fffejUPAcztnLN4BBV`, role result `done`, driver exit 0, GUI listed.
- The sole assigned command returned exactly `PRESENT`, exit 0: the harmless process-local marker reached the verifier shell. No PostgreSQL setting or credential was read or printed; no file, service, database, or test was changed or accessed.
- Service `http://127.0.0.1:28894`; model `-`; cost `$0`; tokens in `8774`, out `436`, cache-read `4800`. Ledger `C:\Users\ANHVU\.opencode\role-runs\board.jsonl`; run directory `C:\Users\ANHVU\.opencode\role-runs\runs\2026-11-03T03-58-38-verifier-chpmis-018-f1-t1-opencode-environment-di-8e11`.
