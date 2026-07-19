# Aven — Backend Integration TODO

Track: **Referral Copilot** (Data Legend / Databricks challenge). Front end is
complete and wired to a backend *seam* that already speaks the required tools'
shapes. Every integration is a **stub that falls back to seeded demo data**, so
the app runs today and lights up as each item below is filled in.

The frontend calls **only** `src/backend/service.py`. Never call a Databricks
tool from `app.py` directly. Fill the stubs; the UI does not change.

## Where things live

| Concern | File | Status |
|---|---|---|
| Config from env / resources | `src/backend/config.py` | ✅ reads env, treats `TODO_...` as unset |
| Service facade (orchestration) | `src/backend/service.py` | ✅ live path written, falls back to demo |
| Mosaic AI Vector Search | `src/backend/vector_search.py` | ⛔ stub → returns `None` |
| Agent Bricks (extract + trust) | `src/backend/agent_bricks.py` | ⛔ stub → returns `None` |
| Genie (NL data tasks) | `src/backend/genie.py` | ⛔ stub → returns `None` |
| MLflow 3 tracing | `src/backend/tracing.py` | ✅ no-op until configured |
| Lakebase persistence | `src/backend/lakebase.py` | ✅ local-JSON fallback |
| Domain rules / ranking | `src/domain.py` | ✅ done (pure) |
| Databricks SQL repo | `src/databricks_adapter.py` | ✅ query written, needs executor |
| Seeded demo data | `src/demo_adapter.py` | ✅ fallback |

## Environment variables (set as Databricks App resources)

All optional; blank or `TODO_...` = that tool is treated as unavailable.

```
DATABRICKS_SERVER_HOSTNAME     # SQL warehouse
DATABRICKS_HTTP_PATH           # SQL warehouse
AVEN_CATALOG / AVEN_SCHEMA     # Unity Catalog location of facility tables
AVEN_VECTOR_SEARCH_ENDPOINT    # Mosaic AI Vector Search endpoint
AVEN_VECTOR_SEARCH_INDEX       # index over the 10k rows
AVEN_SERVING_ENDPOINT          # Agent Bricks / FM serving endpoint
AVEN_GENIE_SPACE_ID            # Genie space over the facility tables
AVEN_LAKEBASE_URL              # Lakebase Postgres connection
AVEN_MLFLOW_EXPERIMENT         # MLflow experiment path
```

`service.backend_mode()` returns `"live"` once Vector Search **and** Agent
Bricks are configured; otherwise `"demo"` (the UI shows an honest banner).

## What to implement, in priority order

1. **Data contract (Databricks team handoff).** Confirm catalog/schema/table
   names and the row shape. Update the query in `databricks_adapter.py`
   (`_FACILITY_QUERY`) and the row mapping in `vector_search.py` to real columns:
   `facility_id, display_name, capability, procedure, equipment, description,
   source_url, source_row_id, latitude, longitude`. Evidence must stay
   **row-level** (source column + row id + literal span).

2. **Mosaic AI Vector Search** — `vector_search.py::retrieve()`.
   Build an index over `description + capability + procedure + equipment`; query
   by capability (+ geocoded location once available); return raw rows with ids
   and source columns. Return `None` on any failure so demo still works.

3. **Agent Bricks** — `agent_bricks.py::assess_claims()`.
   Serve the extraction/scoring agent; for each row extract the capability claim
   and its **literal supporting span**, then set `EvidenceStatus` via
   `domain.evidence_status(...)`. Populate `missing_fields` honestly so a **data
   desert ≠ medical desert**. Never invent a capability (Validator / self-
   correction, brief stretch #2). Output `domain.FacilityCandidate` objects —
   `service._live_plan_routes` already ranks and renders them.

4. **Lakebase** — `lakebase.py`.
   UPSERT/read the user profile (history, saved referrals, ratings, blocklist)
   keyed by email. Keep the local JSON write as an offline mirror. Consider
   promoting saved shortlists + facility overrides into their own tables.

5. **MLflow 3 tracing** — `tracing.py`.
   Attach inputs/outputs + token-cost attributes to each span so the demo can
   show extraction → scoring → ranking **with receipts** (brief stretch #1).

6. **Genie** — `genie.py::ask()`.
   Wire NL → governed SQL for planner questions and regional coverage; surface
   the generated SQL as part of the evidence trail.

7. **Geocoding / distance.** `src/maps.py` exists; feed real `distance_km` into
   `FacilityCandidate` so ranking's travel weighting is meaningful.

## Frontend follow-ups (small)

- **Intake fields for validation.** `domain.validate_confirmed_intake` needs
  `medication_name` + `has_current_prescription` (refill) and
  `has_clinician_order` (lab). Collect these in `show_intake()` and pass them in
  the `request` dict; map them in `service._intake_from_request`.
- **`vaccination` capability.** Added to `demo_adapter.CARE_TASKS` and
  `domain._CARE_TASKS`. Confirm the dataset expresses immunization as a
  capability/service string so retrieval can match it.
- **Ratings/blocklist → trust.** Today the blocklist only filters the UI. Decide
  whether a user's "never refer me here" and low ratings should also feed the
  planner's ranking (a personalization signal, kept separate from facility
  evidence so it never fabricates capability).

## Deploy

- App entry: `apps/referral-copilot/app.py`; deploy config: `app.yaml`.
- Uncomment deps in `requirements.txt` (mlflow, databricks-vectorsearch) as each
  integration lands. Must run on **Databricks Free Edition**.
- Secrets/resources come from the Databricks App, not source. Do not commit
  `.env` or `.aven_profiles.json` (already gitignored).
