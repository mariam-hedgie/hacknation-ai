# Handoff: Databricks team

## Your mission

Build and deploy **Aven**, the working Data Legend Referral Copilot, on Databricks.
Your work is the trusted product backbone: source data, evidence receipts,
shortlist logic, saved plans, and the live Databricks App.

You do **not** need to build a generic chatbot, clinical diagnosis engine,
real-time scheduling system, pharmacy inventory system, or all-India travel
planner.

## Required reading order for the Databricks agent

Read these in order before writing code, creating tables, or changing product
scope. Do not substitute a summary for the official brief.

1. [`reference/data-legend-original-brief.pdf`](reference/data-legend-original-brief.pdf)
   - **Why:** official challenge rules, chosen mission, data expectations,
     required deployment, and judging rubric. This wins if any local document
     conflicts with it.
2. [`../AGENTS.md`](../AGENTS.md)
   - **Why:** shared non-negotiables: focused workflow, evidence/uncertainty,
     decision checkpoints, secret handling, and agent responsibilities.
3. [`final-product-plan.md`](final-product-plan.md)
   - **Why:** exact product behavior, conversational task flows, patient-facing
     language, safety boundaries, and what must not be claimed.
4. [`databricks-execution-plan.md`](databricks-execution-plan.md)
   - **Why:** full data architecture, table contracts, verification gates,
     GitHub synchronization, and deployment sequence.
5. This document, `databricks-team-handoff.md`
   - **Why:** the team's owned deliverables and concrete first actions.

Then read only the official Databricks pages relevant to the next task:

| Task | Specific official documentation |
|---|---|
| Create/deploy the app | [Databricks Apps overview](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/) and [deploy from Git](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy) |
| Start a Streamlit app | [Streamlit App tutorial](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit) and [`app.yaml` runtime configuration](https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/app-runtime) |
| Attach SQL/tables/secrets | [Add resources to a Databricks App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources) |
| Persist plans and notes | [Add a Lakebase resource to an App](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase) |
| Confirm Free Edition capability | [Free Edition overview and limits](https://docs.databricks.com/aws/en/getting-started/free-edition) |
| Govern tables/lineage | [Unity Catalog overview](https://docs.databricks.com/aws/en/data-governance/unity-catalog) |

Do not begin with Agent Bricks, MLflow, Vector Search, or a model-serving
endpoint. Read their specific documentation only after the platform, raw table,
Evidence Receipt, shortlist, and persistence gates are working.

## What success looks like

A user opens a **live Databricks App**, types or speaks a known care need,
confirms the extracted request, sees a small evidence-backed shortlist, opens
an Evidence Receipt containing literal source text and unknowns, saves a plan
with a note, reloads, and sees that plan again.

The app must visibly use the challenge data. It must not make a facility claim
without showing where it came from.

## Exact platform setup

### 1. Make the App exist first

In the Databricks workspace:

1. Open the app switcher -> **Databricks Apps**.
2. Create a tiny Streamlit or Gradio hello-world app.
3. Open its generated URL and verify it loads.
4. Create the real custom app with a neutral technical name such as
   `referral-copilot` (the public product name is **Aven**; keeping the
   technical identifier neutral prevents a later brand change from breaking the
   deployment URL or resources).
5. Configure it to deploy from this GitHub repository, with source path:
   `apps/referral-copilot`.

Databricks Apps runs the deployed product in the workspace; source code can be
developed locally/GitHub and then deployed there. It supports Git deployment
and Python frameworks such as Streamlit and Gradio. See the official
[Apps overview](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
and [Git deployment guide](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy).

### 2. Create/attach App resources in the UI

Use the App's **Resources** section instead of embedding IDs, credentials, or
personal access tokens in code.

| Resource | Permission needed | Why |
|---|---|---|
| SQL warehouse | Can use | App queries the derived facility tables. |
| Unity Catalog table(s) | Select | App reads facilities/evidence/ranking results. |
| Lakebase database | Can connect and create | App persists plans, notes, and feedback. |
| Secret | Read/use only | Optional ElevenLabs key, if voice is added. |
| MLflow experiment | Read only initially | Optional trace viewer; never a prerequisite. |

Each App has a service principal. Use that managed identity. Never put a
personal token or database password in the repository. Apps resources are the
recommended way to provide secure, portable access and permissions. [Databricks
resource documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources)

### 3. Add the minimum app files to this repository

Create these files under `apps/referral-copilot/`:

```text
apps/referral-copilot/
  app.py
  app.yaml
  requirements.txt
  src/
    intake.py
    ranking.py
    evidence.py
    persistence.py
    safety.py
  tests/
```

Start with these exact minimal contents:

`requirements.txt`

```text
databricks-sdk
databricks-sql-connector
streamlit
pandas
```

`app.yaml`

```yaml
command: ['streamlit', 'run', 'app.py']
env:
  - name: 'STREAMLIT_GATHER_USAGE_STATS'
    value: 'false'
```

This is the current official Streamlit starting pattern. Add dependencies only
when the code actually uses them. [Official Streamlit tutorial](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/tutorial-streamlit),
[app.yaml reference](https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/app-runtime)

## Data work you own

### Source table: never mutate it

Create:

```text
<catalog>.referral_copilot.facilities_raw
```

It contains the original challenge rows plus ingestion metadata. Do not clean
over the raw source. You may add normalized/derived tables, but preserve the
ability to point every displayed claim back to original fields and source rows.

### Required derived tables

```text
facilities_normalized
facility_claims_evidence
facility_trust_assessment
saved_care_plans          # Lakebase preferred
shortlists                # Lakebase preferred
user_notes_overrides      # Lakebase preferred
access_feedback           # optional stretch
evaluation_cases
```

Required fields for the key evidence table:

```text
facility_id
capability
source_column
literal_source_text
cited_span
source_row_id
extraction_method
```

**Hard rule:** before rendering an Evidence Receipt, verify that `cited_span`
is literally present in `literal_source_text`. If it is not, discard it. An LLM
may help find a sentence but cannot be the source itself.

### Data-status labels

Use only these concepts in the product:

| UI label | Meaning |
|---|---|
| Documented in facility records | Source text supports the claim. |
| Details disagree - call first | Relevant records conflict. |
| We could not confirm this | Dataset does not establish the claim. |
| Official external source | Separate official source, URL/date shown. |

Never render `not documented` as `not available`.

## Planner logic you own

The conversational layer will send a confirmed, structured request. Do not
rank a facility before confirmation.

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
  "user_confirmed": true
}
```

Implement a deterministic shortlist:

1. Find source-backed capability matches.
2. Calculate distance only when coordinates are valid.
3. Apply visible weights for travel tolerance and facility preference.
4. Penalize conflicting evidence and show missing fields.
5. Return up to three intentionally different options:
   - best documented fit;
   - lower-burden/public-preference option;
   - option needing verification.
6. Return ranking factors and Evidence Receipt data with every option.

`budget_sensitivity` is **not** a fee calculator. It may only affect ranking
through real fields, such as documented facility type, if the dataset supports
that interpretation. Do not invent costs, coverage, or eligibility.

## Persistence contract

Lakebase is the preferred state store. Attach it as an App resource and create:

```text
saved_care_plans(plan_id, demo_user_id, query_id, selected_facility_id,
                 care_task, next_steps, user_language, created_at, updated_at)

user_notes_overrides(override_id, plan_id, facility_id, user_note,
                     selected_despite_rank, created_at)
```

User notes must never modify `facility_claims_evidence` or a facility trust
score. Lakebase is intended for PostgreSQL-backed app state that persists across
deployments. [Lakebase App resource documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)

## What the rest of the team gives you

| Input | Needed from | When |
|---|---|---|
| One fixed capability taxonomy and two seeded scenarios | Product lead | Before ranking logic |
| Patient wording and safety copy | Product/UX | Before action-plan screen |
| Chat extraction schema | AI engineer | Before intake integration |
| Voice integration decision | AI/UX | Only after text flow works |
| Brand/name/UI styling | Product/UX | Can change independently of technical app name |

## What you return to the rest of the team

1. The live App URL.
2. Exact catalog/schema/table names and resource keys.
3. A documented response shape for `get_shortlist(confirmed_request)`.
4. Two seeded case IDs and their expected results.
5. A save/reload demo account or deterministic demo flow.
6. Any unavailable dataset fields/features, stated clearly.

## Build order

1. **Platform proof:** hello-world App deploys from GitHub.
2. **Data proof:** `facilities_raw` loads; profile queries run.
3. **Trust proof:** one facility/capability opens a literal Evidence Receipt.
4. **Product proof:** confirmed request returns a source-backed shortlist.
5. **Persistence proof:** save, reload, reopen.
6. **Integration proof:** conversational UI sends the confirmed request object.
7. **Polish only after all above:** voice, map, MLflow trace viewer, external
   cross-checks, or richer travel estimates.

## Before declaring done

- [ ] Deployed App URL works in a fresh browser session.
- [ ] App reads challenge-derived data through App resources.
- [ ] Every shown claim has a literal source span or an explicit unknown label.
- [ ] Conflicting and missing records have seeded tests.
- [ ] User can save a plan/note and reopen it after reload.
- [ ] No personal token, API key, raw data, or patient data is in GitHub.
- [ ] Text-only demo works if voice/external services fail.
- [ ] Final App is deployed from a specific Git commit, not an untracked edit.
