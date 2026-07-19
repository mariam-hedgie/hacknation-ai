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
| UI façade | `src/ui_contract.py` | ✅ sole planning entry point; safety gates run, delegates to `backend.service.plan_routes` |
| Approved translations | `src/localization.py` | ✅ 21 keys; owns all safety/evidence/trust copy — ⚠️ new translations need native review |
| Trust receipts | `src/trust.py` | ✅ rendered in the Evidence Receipt via `enrichment.assess_record()` |
| Extractor output schema | `src/enrichment.py` | ✅ normalizes the Agent Bricks schema for display |

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

## UI façade adoption (`src/ui_contract.py`)

Restored from `mariam` along with `localization.py` and `trust.py` — five of that
branch's commits had never landed here. `app.py` now depends on the façade for
`service_status()`, `travel_capabilities()`, voice status, and the bounded
feedback vocabulary.

- **✅ Planning seam — resolved.** `app_logic.evaluate_confirmed_request` (was
  `evaluate_demo_request`) now takes an injected `planner`, defaulting to
  `build_demo_options`. `ui_contract.confirm_and_plan` passes
  `backend.service.plan_routes`, so the gates live in one place and the live
  Databricks path is kept — `plan_routes` still falls back to seeded demo
  options on its own when the pipeline is unavailable.
- **✅ Safety gates now run.** `show_confirmation` calls
  `ui_backend().confirm_and_plan()`; only `PROCEED` advances to the results
  stage, and `show_safety_branch()` renders the other three. The planner is
  unreachable behind a gate — `tests/test_ui_contract.py` asserts it is never
  called for a blocked branch, and `test_ui_contract_alignment.py` fails if
  `app.py` ever calls `backend.plan_routes` directly again.
  - Note: the `emergency` branch is a backstop, not the primary path. The
    intake panel still short-circuits on its own checkbox (`app.py`), and the
    urgency slider offers only Routine/Soon/Urgent, so `urgency == "emergency"`
    cannot be selected. Making the emergency question universal across care
    tasks — not just `symptom_first` — is still open.
- **Persistence and auth conflict.** `SessionLocalPlanStore` (plan_id /
  demo_user_id) vs `src/profiles.py`; `mariam`'s `auth.py` (pseudonymous owner
  ID, never stores email) vs `app.py`'s `do_login` (stores name + email). See
  `docs/security/login-and-persistence-audit.md`. Team decision needed.
- **✅ `trust.py` is wired.** `enrichment.assess_record()` bridges the extractor
  schema to `trust.assess_claim`: each claim group is a distinct source field, so
  corroboration counts groups (not repeated spans in one group), and a conflict
  outranks otherwise-good evidence. The Evidence Receipt shows the level and its
  explanation as a neutral chip, plus groups with no verified span under "What we
  could not confirm". The three seeded facilities exercise `strong` /
  `not_established` / `conflicting`.
  - Known limit, documented in `enrichment._claim_evidence`: the extractor gives
    one flat span per claim, not the facility's raw record, so nothing here
    re-verifies a span against original source text. That check belongs in
    `agent_bricks` and does not exist yet.
- **⚠️ New translations need a native reviewer.** The 15 keys added for the
  emergency panel, evidence statuses, and trust levels were machine-drafted.
  `localization.py` is called *approved* translations; these are not approved
  until a Hindi and a Marathi speaker sign them off. Highest priority: the three
  `emergency_*` keys.

## Frontend follow-ups (small)

- **✅ Intake fields for validation — done.** `show_intake()` now collects
  `medication_name` + `has_current_prescription` (refill checkbox) and
  `has_clinician_order` (lab radio: Yes / Not sure / No, where only an explicit
  *No* blocks) and passes them in the `request` dict. Labels are translated in
  all three languages; the radio's stored values stay canonical.
  `service._intake_from_request` maps them onto `IntakeRequest` too, so the live
  pipeline's own `validate_confirmed_intake` call sees them.
- **`vaccination` capability.** Added to `demo_adapter.CARE_TASKS` and
  `domain._CARE_TASKS`. Confirm the dataset expresses immunization as a
  capability/service string so retrieval can match it.
- **The language picker is still mostly a facade.** `?lang=` now resolves through
  `localization.resolve_language` and an unsupported language falls back to
  English *visibly*. But `LANDING_COPY` is English-only (`tx()` silently falls
  back), and every label in `show_intake()` is hardcoded English — so switching
  to हिंदी changes the eyebrow, step chips, and footer boundary, and nothing
  else. `STRINGS["tagline"]`, `["promise"]`, and `["vitals"]` are translated but
  never rendered — dead keys. Biggest visible frontend gap.
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
