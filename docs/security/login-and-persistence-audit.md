# Login and persisted-information security audit

**Audit date:** 2026-07-19

## Verdict

Aven must not implement a separate password database for this hackathon.
Databricks Apps already initiates OAuth authentication and restricts access with
App permissions. The application should consume the authenticated proxy user,
turn it into a pseudonymous owner ID, and scope every Lakebase operation to that
owner.

The React app now uses authenticated FastAPI save/list/delete/feedback routes.
In Databricks mode those routes derive a pseudonymous owner from the trusted
proxy header and use owner-scoped Lakebase SQL with rotating OAuth database
credentials. Local-demo state is process-local and visibly disposable. The
durable path is **not deployment-verified until its cross-session and two-user
checks pass in Databricks Free Edition**.

## Findings and remediations

| Area | Before this audit | Remediation | Status |
|---|---|---|---|
| Interactive login | No custom login; deployment assumptions were undocumented | Keep Databricks OAuth as the login boundary; never collect an Aven password | Design PASS; workspace check required |
| Missing/spoofed identity | No reusable identity validation | `src/auth.py` accepts `X-Forwarded-User` only in explicit Databricks mode and rejects missing, duplicated, oversized, or control-character values | Test PASS |
| Personal identifiers | Durable design could have used email/demo user ID | HMAC-SHA256 produces an app-scoped owner ID using a secret pepper; raw user ID and email are not retained | Test PASS |
| Anonymous demo mode | Could be accidentally reused during deployment | Local mode requires two explicit flags and is rejected when Databricks deployment markers exist | Test PASS |
| Cross-user access/IDOR | Lakebase primary key was only `plan_id` | Every query now binds `owner_id`; the database uses `(owner_id, plan_id)` as the key and foreign key | Test PASS; Lakebase check required |
| Data minimization | The UI handoff shape includes the full confirmed request, possibly including medication, location, and free text | Durable storage allow-lists the saved decision, selected option, next steps, and override; it discards `confirmed_request`, `original_text`, medication, email, and demo-user fields | Test PASS |
| Free-text safety | Persistence accepted arbitrary feedback/status content up to the overall JSON limit | Statuses are allow-listed; notes are plain text, limited to 500 characters, and reject control characters | Test PASS |
| SQL injection | Values were already bound | Owner IDs and all user values remain parameters; table names are strict identifiers | Test PASS |
| Record deletion | No deletion operation | An owner-scoped delete removes the plan and cascades only its feedback | Test PASS |
| Retention | Records had no expiry | Plans expire after 30 days; safe app initialization purges expired plans and cascades their feedback | Code/schema PASS; live startup check required |
| Legacy schema | Re-running `CREATE TABLE IF NOT EXISTS` could silently preserve the unsafe plan-ID-only table | Schema now aborts when it detects that legacy table without `owner_id` | SQL review PASS; workspace check required |
| React persistence wiring | UI previously used a browser email/local JSON profile path | Custom login/profile endpoints were removed; My plans uses authenticated `/api/plans`, and save is shown complete only after server confirmation | Test/build PASS; live Lakebase check required |
| Database credentials | No production executor existed | The server consumes managed `PG*` coordinates and requests a fresh App service-principal OAuth database token for each operation | Test PASS; workspace permission check required |

## Required Databricks wiring

1. Limit App permissions to the team, judges, or intended testers using **CAN
   USE**. Do not grant ordinary app users **CAN MANAGE**.
2. Set `AVEN_AUTH_MODE=databricks` as a static, non-secret App environment
   value.
3. Create at least 32 random bytes for `AVEN_IDENTITY_PEPPER`, store it as a
   Databricks secret resource, and expose it with `valueFrom`. Never put it in
   Git or plain `app.yaml`.
4. The FastAPI request boundary already calls:

   ```python
   identity = resolve_identity(request_headers, os.environ)
   store = PersistentSqlPlanStore(executor, owner_id=identity.owner_id)
   ```

   Do not add an `owner_id` field to any browser request.
5. Attach Lakebase under the resource key `postgres`. App startup safely creates
   the same schema as `databricks/lakebase_schema.sql`; if either path raises the legacy-schema error,
   migrate or recreate the hackathon-only tables; do not bypass the error.
6. Do not persist the original conversation, symptom text, medication name,
   home address, email, voice audio, transcript, or API/tool logs. Persist only
   the shortlist decision and optional user-authored note.
7. Verify the app-start `purge_expired()` call can delete an expired synthetic
   plan. A separate scheduled Lakebase job is optional resilience, not a reason
   to extend retention.
8. Keep detailed exceptions server-side and show a generic login/save failure
   to the user. Never log headers, plan payloads, notes, or database credentials.

## Deployment tests that must pass

- [ ] Unauthenticated/incognito request is redirected to Databricks login or
  denied; the app never invents a demo user.
- [ ] A user without **CAN USE** receives access denied.
- [ ] Missing `X-Forwarded-User` yields no app content or persistence call.
- [ ] Two signed-in test users may reuse the same `plan_id` and see only their
  own plan and feedback.
- [ ] User A cannot read, update, list, or delete User B's record even when the
  plan ID is known.
- [ ] Database inspection shows pseudonymous `owner_id`, not raw email or the
  Databricks user header.
- [ ] Saved JSON excludes confirmed request, medication, original text, home
  location, email, transcript, and voice audio.
- [ ] Deleting a plan removes its feedback but not another user's same-named
  plan.
- [ ] An expired synthetic plan is purged.
- [ ] Rotating the identity pepper is treated as a data migration; changing it
  without migration would make prior records inaccessible.

## Important boundary

This is a hackathon privacy/security baseline, not a claim of HIPAA, DPDP Act,
or clinical-system compliance. Use synthetic demo users and data. A real patient
deployment would require legal/privacy review, consent, breach response,
auditing, stronger retention controls, and a documented data-processing basis.

Current official platform references:

- [Databricks App HTTP identity headers](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/http-headers)
- [Databricks App authorization model](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/key-concepts)
- [Databricks App security best practices](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/best-practices)
- [Lakebase App resources](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
