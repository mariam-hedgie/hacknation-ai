# Production authentication and data plan

## Current state

When deployed as a Databricks App, Aven uses the platform's OAuth boundary and
derives a pseudonymous server-side owner ID before any saved-plan operation.
That is a real authentication design, but it is specific to Databricks Apps.
Local-demo mode is deliberately disposable and is not production login.

## Standalone production target

Use one OpenID Connect provider with Authorization Code + PKCE. The backend,
not the React app, validates issuer, audience, expiry, signature/JWKS, nonce,
and state. Map the verified provider subject to an HMAC-derived internal owner
ID; do not store raw email in plans. Keep the session in Secure, HttpOnly,
SameSite cookie(s), use CSRF protection for state-changing requests, and apply
shared-store rate limits to intake, search, and feedback endpoints.

Before choosing a vendor, test account linking, duplicate accounts, logout,
deletion, recovery, revocation, expiry, and two-user isolation. A provider
client secret belongs only in the deployment secret manager. Do not implement a
separate password database.

## Separate data products

| Data | Store | Rule |
|---|---|---|
| Facility evidence | governed source table | immutable, literal evidence only |
| Address candidates | `facility_address_candidates` ledger | web discovery only; review required |
| Verified branches | `facility_branch_locations` table | source URL, retrieval time, reviewer, coordinates |
| Saved plans | owner-scoped database | allow-listed decision only; no raw health narrative |

Add the branch table through a forward-only migration. Add nullable address
columns/table first, backfill in small batches, then add indexes. Never modify
an already-applied migration or overwrite an evidence row with discovered web
data. See `apps/referral-copilot/docs/address-enrichment-runbook.md` for the
candidate-to-verified workflow.

## Ollama deployment boundary

For local development, Ollama runs at `127.0.0.1:11434`. For production, run it
as a private service on the same trusted network as the backend, with a timeout,
model pin, health check, capacity limit, and a manual-form fallback. Do not
expose Ollama directly to browsers and do not treat its structured draft as
evidence or a medical decision.
