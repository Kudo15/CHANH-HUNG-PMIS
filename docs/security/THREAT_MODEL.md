# Threat Model — Initial STRIDE Pass

Scope: proposed local MVP and first vertical slice. This is an initial inventory, not a completed security assessment; revisit after identity/session and authorization policy are chosen.

| Threat | Example | Initial control / evidence |
|---|---|---|
| Spoofing | Stolen/forged session accesses PMIS | Approved session design; expiry/revocation tests |
| Tampering | Unauthorized project/task/status change | Server-side grants/scope/transition checks; negative API tests |
| Repudiation | Assignment/state change cannot be attributed | Audit actor/action/target/time; approved access/retention |
| Information disclosure | Guessed ID or aggregate leaks another department's data | Deny by default; scoped item/list/dashboard tests; non-disclosing errors |
| Denial of service | Large listing or auth attempts exhaust service | Pagination/limits, rate/resource controls; numeric limits TBD |
| Elevation of privilege | Client-supplied role bypasses controls | Explicit grants, server-side scope resolution, separation-of-duties review |
| Storage exposure | Future document URL bypasses restriction | Backend upload/download checks; signed access only after policy approval |
| Supply chain/config | Secret or vulnerable dependency committed | Secret/dependency review, `.env` ignored, CI checks |
| AI data leakage | Sensitive record sent to external provider | AI excluded from MVP; provider/data approval and redaction required |
| Unsafe deployment | Dev service exposed publicly | Localhost-only binding; deployment Human Gate |

## Verification focus
Cover unauthenticated/inactive identity, cross-project read/write, department boundary, unauthorized list/dashboard aggregate, invalid transition, missing audit event, secret/log leakage, and disabled external AI access. Likelihood, severity, and residual risk need deployment context.
