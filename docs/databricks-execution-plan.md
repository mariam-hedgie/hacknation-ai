# Databricks execution plan: Referral Copilot

## Outcome

This is the implementation playbook for **Aven**, the final Data Legend entry. It
connects the Databricks platform, GitHub codebase, conversational intake,
evidence logic, persistence, and demo workflow in
[`final-product-plan.md`](final-product-plan.md).

The original challenge PDF remains the source of truth. This plan selects the
smallest architecture that meets the Referral Copilot requirements and is
reliable in a 24-hour hackathon.

## Architecture

```text
GitHub repository
  - app source, SQL/Python transforms, tests, docs, synthetic fixtures
  - never raw challenge data, secrets, or patient information

Databricks Free Edition
  - governed source and evidence tables
  - transparent ranking/query logic
  - Lakebase persistence for plans and feedback
  - deployed Databricks App

Optional external services
  - ElevenLabs for explicit voice input/read-back
  - Tavily for narrowly scoped official-source cross-checks
  - never raw challenge data or personal health data
```

The app is deployed on Databricks, rather than as a separate site that merely
links to Databricks. GitHub is the source of code; Databricks is the source of
data, execution, persistence, and the demo URL.

Databricks Apps supports Python or Node.js apps, integrates with Unity Catalog
and SQL, and can deploy directly from Git. Read the official
[Apps overview](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
and [deployment guide](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy).

## UI and code decision

For this hackathon, use a thin **Python + Streamlit or Gradio** Databricks App.
Choose whichever official template the team gets deployed first; do not add a
custom React/FastAPI stack unless a team member has already deployed it in
Databricks Apps.

```text
apps/referral-copilot/
  app.py
  app.yaml
  requirements.txt
  src/intake.py          # task classification and confirmation card
  src/evidence.py        # receipt assembly
  src/ranking.py         # explainable ranking
  src/persistence.py     # saved plans, notes, feedback
  src/safety.py          # output allow-list and emergency branch
  tests/
```

First deploy a hello-world template. That proves the workspace, App, and
deployment path before product work starts. The current Apps getting-started
guide covers template creation and iteration:
[Databricks Apps getting started](https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/get-started).

## Gate 0: environment check

Complete these in the first 30 minutes. Assign one owner and record results.

| Check | Done when | If blocked |
|---|---|---|
| Workspace | Shared Free Edition workspace opens | Use organizer-provided access; do not settle for local-only. |
| Apps | Hello-world App URL loads | Escalate to organizers: a live App is required. |
| Unity Catalog | Team can create/query a table | Record available catalog/schema names. |
| Challenge data | Approved data file is accessible in workspace | Do not commit or export the file. |
| Lakebase | App can attach a database resource | Use a durable Databricks table only if track rules permit. |
| Git | App can deploy from this GitHub repo | Workspace-folder deploy is temporary fallback only. |
| Permissions | App reads data and writes saved-plan state | Grant minimum resources and re-test. |

Free Edition is serverless and quota-limited, so test actual feature access
early. [Free Edition overview](https://docs.databricks.com/aws/en/getting-started/free-edition)

## Phase 1: data ingestion and profiling

### Create a project schema

Use one agreed project namespace, for example:

```sql
CREATE SCHEMA IF NOT EXISTS <catalog>.referral_copilot;
```

Write actual catalog/schema values in `apps/referral-copilot/README.md` rather
than hard-coding them throughout the app.

### Preserve the raw source

Load the provided dataset once into `facilities_raw`. Keep original fields,
source row ID, source file, ingest timestamp, and row hash. Never overwrite a
raw value to make it look more trustworthy.

```text
<catalog>.referral_copilot.facilities_raw
  source_row_id, source_file, ingested_at, source_row_hash, original columns
```

### Profile before designing features

Use SQL/notebooks to determine actual coverage for facility IDs, coordinates,
capability, procedure, equipment, description, provider counts, facility type,
contact details, and source URLs. Also check duplicates, conflicts, and nulls.

The profile decides scope. If price, pharmacy, language, appointment, transport,
or lodging fields are absent, the app says `not documented`; it must not infer
them. Commit only the profiling code and aggregate findings, never data extracts.

## Phase 2: traceable data products

Query precomputed, inspectable tables in the app. Do not ask a model to reread
10,000 records live during the demo.

```text
facilities_normalized
  facility_id, display_name, location, lat, lon, facility_type, source_row_id

facility_claims_evidence
  evidence_id, facility_id, capability, source_column, literal_source_text,
  cited_span, span_start, span_end, extraction_method, source_row_id

facility_trust_assessment
  facility_id, capability, corroboration_count, contradiction_flag,
  missing_fields, data_status, explanation

demo_route_estimates
  scenario_id, facility_id, travel_mode, estimated_time, estimated_cost,
  provenance='seeded_demo_estimate'

evaluation_cases
  case_id, confirmed_care_task, expected_status, expected_facility_ids
```

### Evidence contract

For every displayed capability:

1. Begin with a real source field/row.
2. Extract a candidate sentence/span.
3. Verify that the exact cited span occurs in stored raw text.
4. Store the source column and source-row identifier.
5. Discard citations that fail literal-span verification.

Models may locate a candidate span, but a model output is never evidence on its
own. Use statuses rather than clinical-quality scores:

```text
documented            source record supports the claim
conflicting           relevant records disagree
not_documented        data does not establish the requested fact
external_corroborated official source supports it; show URL and retrieval date
```

`Not documented` never means `not available`.

## Phase 3: conversational planning logic

Natural-language voice/text is the front door. It creates an editable object,
and the user or clinician confirms it before search or ranking.

```json
{
  "care_task": "known_referral | procedure | lab | refill | symptom_first | follow_up",
  "confirmed_capability": "string or null",
  "location": "string / coordinates",
  "urgency": "routine | soon | urgent | emergency",
  "travel_tolerance": "low | medium | high",
  "budget_sensitivity": "low | medium | high",
  "facility_preference": "public | private | either | unknown",
  "language_preference": "string or null",
  "needs": ["accessibility", "caregiver", "documented_contact"],
  "user_confirmed": true
}
```

### Deterministic shortlist

1. Filter to source-backed capability matches.
2. Calculate distance only with valid coordinates.
3. Apply visible travel/budget/preference weights.
4. Penalize conflicting evidence; surface missing data without treating it as
   proof of absence.
5. Return distinct choices where possible: best documented fit, lower-burden
   route, and an alternative that needs verification.
6. Save ranking factors and create an Evidence Receipt for each option.

Budget sensitivity can affect ranking from real fields such as facility type
only if the data supports that relationship. It must never invent a price.

### Safety boundaries

- Symptom-first requests use a fixed emergency-warning branch. A reported
  warning stops normal ranking; an LLM alone does not decide this path.
- Refill/pharmacy flows never prescribe, change a dose, suggest substitutions,
  or infer stock.
- Lab flows only show preparation/order instructions from an official source.
- Follow-up flow shows appointment links or hours only from supported sources;
  otherwise it says `call to confirm`.

## Phase 4: persistence

Attach Lakebase as a Databricks App resource, if available, for interactive
state:

```text
saved_care_plans
shortlists
user_notes_overrides
access_feedback
```

Lakebase is PostgreSQL-backed and retains state across deployments. Use the
managed App resource/identity rather than a hard-coded password or connection
string. [Lakebase resource documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)

Keep data types separate:

| Source evidence | User state |
|---|---|
| Immutable raw/derived Delta tables | Lakebase tables |
| Facility claims and cited spans | Saved plans, notes, overrides |
| Changed only by data pipeline | Changed by user actions |
| Never altered by a note | Never treated as facility truth |

Minimum demo: save a plan and note, reload the app, reopen the same plan.

## Phase 5: app screens and service boundaries

Required screens:

1. Welcome and consent - spoken or typed request, simple safety framing.
2. Targeted questions - task-specific questions only.
3. Confirm request - editable summary; no search until confirmation.
4. Action plan - plain-language next steps and up to three options.
5. Evidence Receipt - source span, conflicts, missing facts, ranking factors.
6. Save/share - shortlist, note, override, reopen.

The default screen answers `What should I do next?`; technical evidence is
available via `Why this option?`, not forced on a stressed user.

| Component | Runs where | Purpose | Fallback |
|---|---|---|---|
| Intake extraction | App backend | Conversation to editable request | Typed fixed-task form |
| Evidence/ranking | Databricks tables/backend | Shortlist and receipts | Seeded tested scenarios |
| ElevenLabs | Backend only | Optional voice input/read-back | Full text flow |
| Tavily | Backend only | Optional official-source cross-check | Dataset evidence only |
| Lakebase | App resource | Saved state | Durable Databricks table if allowed |

Use parameterized queries/SDK calls, never raw chat text in SQL. The deployed
app uses its service principal and resource permissions, never a personal token.
Keys live only in Databricks secrets/configuration, never source or browser code.

## Phase 6: GitHub-to-Databricks synchronization

Commit:

```text
apps/referral-copilot/
databricks/01_ingest_and_profile.sql
databricks/02_build_evidence_tables.py
databricks/03_build_trust_assessment.sql
databricks/04_seed_evaluation_cases.sql
databricks/05_vector_search_setup.md
databricks/lakebase_schema.sql
tests/
docs/
```

Never commit raw challenge data, data extracts, patient/referral/prescription
data, Databricks tokens, external API keys, or database credentials.

Deployment sequence:

1. Push code to GitHub.
2. Create/configure a custom Databricks App from this repository.
3. Set source path to `apps/referral-copilot`.
4. Attach required table permissions and Lakebase resource.
5. Deploy a specific Git commit for the final demo.
6. Run evaluation cases in a fresh browser session and record a backup video.

Git branch deployment is convenient during development. Commit-SHA deployment
is safer for the final demo because it is immutable. See the official
[Git deployment documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy).

## Verification gates

| Gate | Evidence of completion |
|---|---|
| Platform | Hello-world App URL opens. |
| Data | Raw table and profiling query work. |
| Trust | Capability card opens a literal source-span receipt. |
| Unknowns | Missing/conflicting cases label correctly. |
| Planning | Confirmed request creates a shortlist. |
| Persistence | Save/note/reload/reopen works. |
| Conversation | Natural language becomes editable intake. |
| Safety | Emergency branch halts ranking; refill/lab do not prescribe. |
| Deployment | App runs from the final Git commit. |
| Demo | Two seeded cases need no fragile live dependency. |

## 24-hour order

| Time | Do this |
|---|---|
| 0-0.5h | Access check, hello-world app, choose template and two seeded cases. |
| 0.5-3h | Ingest/profile source data; create app shell and care-task schema. |
| 3-6h | Build evidence table, span verification, intake/confirmation UI. |
| 6-10h | Build ranking, action plan, and Evidence Receipt. |
| 10-13h | Attach Lakebase; finish save/note/reopen. |
| 13-17h | Test conflicts/unknowns; add chat and only then voice. |
| 17-21h | Deploy from Git; polish error states and record backup. |
| 21-24h | Fresh-session tests, rehearsal, README, submission. |

## Definition of done

In a fresh session, a user describes a known care need, confirms the extracted
request, gets a plain-language action plan, inspects evidence/unknowns, saves a
note or override, reloads the app, and opens the saved plan. A second seeded
case and an emergency safety case also behave correctly. Anything else is a
stretch feature.
