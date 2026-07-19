# aven Databricks deployment handoff

Give this document to the teammate who owns the Databricks account. It is a
deployment checklist for the existing React + FastAPI app, not a request to
redesign the product.

## Can another teammate deploy it?

Yes. The teammate must have:

- a **Databricks Free Edition** workspace, not a paid organizational workspace;
- access to this Git repository and the commit being submitted;
- permission to create/manage a Databricks App, Lakebase Autoscaling database,
  AI Search endpoint/index, secret scope, and the relevant Unity Catalog data;
- access to the organizer-linked Data Legend dataset.

If Free Edition does not expose one of those products or its quota is exhausted,
record that as a blocker. Do not silently deploy from a paid workspace or claim
that a local fallback is live Databricks evidence.

## What Mariam does before handoff

1. Run the local verification commands in the final section of this document.
2. Review and commit the intended working-tree changes.
3. Push that commit to the repository/branch the teammate can access.
4. Send the teammate:
   - repository URL;
   - branch and exact commit SHA;
   - this document;
   - the official challenge PDF at
     [`reference/data-legend-original-brief.pdf`](reference/data-legend-original-brief.pdf).

Do not send `.env`, API keys, Databricks tokens, database passwords, patient
information, or the identity-pepper value.

## Definition of done

The work is complete only when a fresh signed-in browser can:

1. open the React app in Databricks Free Edition;
2. enter and confirm a location and care need;
3. receive challenge-data candidates with distance, literal row/field evidence,
   gaps, and an explicit save action;
4. save a decision and optional note;
5. close/reopen the app and retrieve that saved decision;
6. keep two signed-in users' plans isolated even when they use the same plan ID.

## Step 1 — clone and inspect the exact commit

```bash
git clone <REPOSITORY_URL>
cd hacknation-ai
git switch <BRANCH>
git pull --ff-only
git rev-parse HEAD
```

The last value must match the SHA Mariam supplied. Do not deploy uncommitted
workspace edits.

Read, in order:

1. [`reference/data-legend-original-brief.pdf`](reference/data-legend-original-brief.pdf)
2. [`../AGENTS.md`](../AGENTS.md)
3. [`compliance/data-legend-official-brief-audit.md`](compliance/data-legend-official-brief-audit.md)
4. [`compliance/final-submission-gate.md`](compliance/final-submission-gate.md)
5. [`security/login-and-persistence-audit.md`](security/login-and-persistence-audit.md)

## Step 2 — confirm the workspace and dataset

In the Databricks UI:

1. Confirm the workspace is labelled **Free Edition**.
2. Open the organizer Marketplace link from page 4 of the PDF.
3. Subscribe to/open the India facilities dataset.
4. Record its full catalog, schema, and table name.
5. Run a row count and schema inspection.

The PDF says 10,000 rows and 51 columns. If the live listing returns a different
count or schema, record the actual result and retrieval time in
[`compliance/final-submission-gate.md`](compliance/final-submission-gate.md).
Do not trim, duplicate, or relabel rows merely to force the advertised count.

## Step 3 — build the active searchable table

The active app reads `workspace.default.facilities_searchable`. The current
pipeline is:

```text
official facilities table
  -> extract_data.py
  -> workspace.default.facilities_consolidated
  -> flatten_data.py
  -> workspace.default.facilities_searchable
```

Important:

- `extract_data.py` performs the expensive full-table consolidation. Verify the
  source table and output SQL before running it.
- `flatten_data.py` preserves the raw source fields, row ID, coordinates, city,
  and validated public/private operator value. Do not remove them.
- `search_text` is the AI Search embedding source.
- A displayed claim is accepted only when its extracted span is found literally
  in the preserved raw source field.

The standalone scripts currently read `SERVER_HOSTNAME`, `HTTP_PATH`, and
`ACCESS_TOKEN` from the operator's local environment. If you use that route,
keep the token only in your ignored local `.env`; never paste it into Git,
screenshots, chat, or `app.yaml`. Prefer Databricks workspace execution or OAuth
where available.

After the table is built, verify:

```sql
SELECT count(*) FROM workspace.default.facilities_searchable;

SELECT
  count_if(unique_id IS NULL OR trim(unique_id) = '') AS missing_row_ids,
  count_if(search_text IS NULL OR trim(search_text) = '') AS missing_search_text,
  count_if(raw_capability IS NULL) AS missing_raw_capability,
  count_if(latitude IS NOT NULL AND (latitude < -90 OR latitude > 90)) AS bad_latitude,
  count_if(longitude IS NOT NULL AND (longitude < -180 OR longitude > 180)) AS bad_longitude
FROM workspace.default.facilities_searchable;
```

Keep invalid/missing values as unknown. Do not guess replacements.

## Step 4 — create AI Search

Follow [`../databricks/05_vector_search_setup.md`](../databricks/05_vector_search_setup.md).
Use these exact names because `app.yaml` references them:

- AI Search endpoint: `aven-facility-search`
- source table: `workspace.default.facilities_searchable`
- primary key: `unique_id`
- embedding source: `search_text`
- App resource key: `facility-evidence-index`
- App permission: **Can select**

Sync the index and run a query that returns at least `unique_id`, raw receipt
fields, coordinates, and the extracted claim fields. Semantic similarity is
only candidate retrieval; it is not evidence by itself.

## Step 5 — create and attach Lakebase

1. Create a Lakebase **Autoscaling** project/database.
2. In the App's Resources section choose **Add resource → Database**.
3. Select the Lakebase database with **Can connect and create**.
4. Set its resource key to exactly `postgres`.

Databricks then injects `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPORT`, and
`PGSSLMODE`. `app.yaml` resolves the endpoint path through `valueFrom: postgres`.
The app generates short-lived OAuth database credentials itself; do not create
or paste a database password.

The server creates the safe owner-scoped tables at startup. You may also review
or run [`../databricks/lakebase_schema.sql`](../databricks/lakebase_schema.sql)
in the Lakebase SQL editor. If it reports a legacy table without `owner_id`,
stop and recreate/migrate that hackathon-only schema—never bypass the check.

## Step 6 — create the identity secret

Generate a value locally:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Store the output in a dedicated Databricks secret scope. Do not send it to
Mariam. In the App Resources section:

1. add that secret with **Can read**;
2. use the exact resource key `identity-pepper`.

`app.yaml` exposes it only to the server as `AVEN_IDENTITY_PEPPER`. Rotating it
later requires a saved-plan ownership migration.

## Step 7 — create and deploy the App

1. Open **Databricks Apps** and create a custom app from the Git repository.
2. Select the exact branch/commit supplied by Mariam.
3. Set the application source directory to `apps/referral-copilot`.
4. Attach:
   - Lakebase resource `postgres`;
   - secret resource `identity-pepper`;
   - AI Search resource `facility-evidence-index`.
5. Grant intended teammates/judges **CAN USE**, not **CAN MANAGE**.
6. Deploy.

Databricks sees the app-root `package.json`, installs Node and Python
dependencies, builds the React workspace, then runs `python run_app.py` from
[`../apps/referral-copilot/app.yaml`](../apps/referral-copilot/app.yaml).

Do not change the command back to Streamlit. The submitted interface is React.

## Step 8 — live verification

Use synthetic demo requests only.

### Evidence check

- Complete the Patna golden path.
- Open all three result cards.
- Confirm each eligible card shows a distance or an explicit unknown state.
- Confirm each documented claim shows a raw field and row ID.
- Confirm missing evidence reads `not documented`/`could not confirm`, never
  `unavailable`.
- Confirm an invalid/fabricated span cannot appear as documented.

### Persistence check

1. User A saves `shared-test-plan` and a harmless note.
2. Refresh and reopen **My plans**; it must still appear.
3. Close the browser, sign in again, and confirm it still appears.
4. User B saves the same plan ID.
5. Confirm A and B see only their own version.
6. Delete A's plan and confirm B's remains.
7. Inspect Lakebase: `owner_id` must be pseudonymous; stored JSON must not
   contain email, location, medication, health intake, transcript, or audio.

### Deployment check

- Open the URL in a fresh browser session.
- Confirm unauthenticated access is redirected/denied by Databricks.
- Confirm the UI says live Databricks evidence only when AI Search is working.
- Record the URL, commit SHA, resource keys, row count, test time, and a
  successful cross-session plan ID in
  [`compliance/final-submission-gate.md`](compliance/final-submission-gate.md).

## What to send back to Mariam

Do not send secrets or tokens. Send:

```text
Workspace confirmed as Free Edition: yes/no
Dataset full table name:
Observed row count and column count:
Searchable table name:
AI Search endpoint/index/resource key:
Lakebase resource key:
Databricks App URL:
Deployed Git SHA:
Cross-session persistence test: pass/fail
Two-user isolation test: pass/fail
Broken receipt test: pass/fail
Any quota/permission/blocker:
```

## Local test commands

From the repository root, one-time setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r apps/referral-copilot/requirements.txt
cd apps/referral-copilot
npm install
npm run build
```

Start the production-shaped React app:

```bash
cd /path/to/hacknation-ai/apps/referral-copilot
source ../../.venv/bin/activate
AVEN_AUTH_MODE=local_demo AVEN_ALLOW_LOCAL_DEMO=true python run_app.py
```

Open <http://localhost:8010>. Local saved plans are process-local; restarting
the server clears them. That is expected and does not test Lakebase.

Run all local checks from the repository root:

```bash
source .venv/bin/activate
python -m unittest discover -s apps/referral-copilot/tests -q
python -m compileall -q apps/referral-copilot
npm test
npm --prefix apps/referral-copilot run build
npm --prefix apps/referral-copilot --workspace frontend run lint
python -m pip check
```

Local success proves the UI, API, safety logic, receipt validation, and
persistence contract. It does not prove Free Edition deployment, live challenge
data, AI Search, or Lakebase cross-session persistence.
