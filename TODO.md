# Aven — Integration TODO

> **2026-07-19 audit notice:** workspace/table/quota observations below are a
> historical handoff and were not reverified during the official-PDF audit.
> Do not treat them as current proof. The authoritative current gates are
> [`docs/compliance/data-legend-official-brief-audit.md`](docs/compliance/data-legend-official-brief-audit.md)
> and [`docs/compliance/final-submission-gate.md`](docs/compliance/final-submission-gate.md).
> React/FastAPI authenticated Lakebase wiring is now complete in the repository;
> live Free Edition, challenge-data, Vector Search, and cross-session proof are
> still open.

Track: **Referral Copilot** (Data Legend / Databricks challenge).

**State of play (2026-07-19, reviewed against the working tree):** the code is in
much better shape than the previous revision of this file claimed. The whole
evidence pipeline — retrieval, mapping, ranking, tracing, Genie — is *written and
tested* (the current count is recorded in the compliance audit). What is missing is **live configuration and
a working warehouse**: nothing is actually running against live data, and
`backend_mode()` returns `demo` on every machine today.

The React frontend calls the FastAPI boundary, which delegates planning to
`apps/referral-copilot/src/backend/service.py`. Never call a Databricks tool
directly from the browser.

---

## 🚨 The things standing between us and a live demo

### Blocker #1 — we moved workspaces, and the new one has no derived tables

The original workspace (`dbc-7e1b9c30`) hit the Free Edition daily compute wall:

```text
BAD_REQUEST: Sorry, cannot run the resource because you have hit your
free daily limit. Please come back again tomorrow.
```

`.env` has been repointed to a **new workspace** (`dbc-67dae7f7`). Verified
today in that new workspace:

- ✅ Credentials work, quota is fresh, `ai_query` works (tested,
  `databricks-meta-llama-3-3-70b-instruct`, 2.4s on 2 rows).
- ✅ The **raw challenge dataset is present**:
  `databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities`
  — **10,088 rows**.
- ⛔ **`workspace.default` is completely empty.** No `facilities_consolidated`,
  no `facilities_parsed`, no `facilities_cleaned`, no `facilities_searchable`.

So the entire derived pipeline has to be re-run here: `extract_data.py`
(`ai_query` consolidation over all 10,088 rows) → `flatten_data.py` /
`database.py`. **That LLM pass over 10k rows is the single most expensive thing
in the project and is the most likely cause of the previous workspace's quota
death.** Treat it as a one-shot: get the SELECT right before running it, and
persist the result immediately.

Two consequences worth deciding explicitly:

- The old workspace may still hold a fully built `facilities_searchable`. If its
  quota has reset, reading from there is far cheaper than rebuilding. **Check
  the old workspace before spending the rebuild.**
- **Do not let the judged demo depend on a live warehouse call.** Cache a real
  sample to a committed fixture (#4) so a mid-presentation quota wall degrades
  to seeded data instead of breaking the story.

### Resolved in repo — flattening now preserves ranking and receipt columns

This is new, and it invalidates a "wontfix" the previous TODO had recorded.

The raw `facilities` table carries columns `facilities_searchable` **throws
away** in `database.py`'s final `SELECT`. Non-null coverage measured today:

| Raw column | Non-null / 10,088 | Currently used? |
|---|---|---|
| `latitude` / `longitude` | 9,970 (98.8%) | ⛔ dropped |
| `address_city` | 10,030 | ⛔ dropped |
| `facilityTypeId` | 10,021 | ⛔ dropped |
| `operatorTypeId` (public/private) | 10,015 | ⛔ dropped |

Consequences:

- **Distance ranking is NOT blocked** — the previous TODO said "no lat/lon
  exists, `distance_km` must stay `None`." That was wrong: coordinates exist for
  98.8% of rows and were simply not carried through the flattening. Fixing the
  `SELECT` unblocks distance ranking and `agent_bricks`'s hardcoded
  `distance_km=None`.
- **`facility_preference` (public/private) is a real ranking input in
  `domain.py`, and the live path cannot honor it** because `operatorTypeId`
  never reaches the app. Same for `facility_type=None` in `agent_bricks`.

Implemented: `flatten_data.py` carries coordinates, city, facility/operator
type, and original description/capability/procedure/equipment fields into
`facilities_searchable`. `agent_bricks` validates evidence against those raw
fields, emits row/column receipts, validates operator type, and calculates an
honestly labelled straight-line distance for supported demo cities. The
corrected table and Vector Search index still need to be rebuilt live.

### Blocker #1c — the raw dataset has column-misaligned rows

`SELECT DISTINCT operatorTypeId` returns, alongside the expected `private` /
`public` / `government`, values that are plainly from **other columns**:

```text
'private', 'public', 'government',
'81.65721130371094',                                  <- a latitude
'{"coordinates":[75.57,31.32],"type":"Point"}',       <- the coordinates column
'["https://www.justdial.com/...", ...]',              <- the source_urls column
'""retinaAndVitreoretinalOphthalmology""'             <- a specialty
```

Some rows are shifted — almost certainly unescaped delimiters in the upstream
CSV. Anything reading `operatorTypeId` must validate against an allowed set and
treat everything else as **unknown**, never guess.

Related, and a good demo beat: the first sampled row is `Aravind Eye Hospital`
with `address_city = 'Hyderabad'` but coordinates `(11.94, 79.49)` — that is
Tamil Nadu, ~500km from Hyderabad. **City and coordinates contradict each
other.** This is exactly the "documented vs conflicting" distinction Aven exists
to surface — do not silently prefer one. It also means distance ranking should
be derived from coordinates and labelled as such, with the city mismatch shown
as a conflict rather than resolved behind the user's back.

### Resolved in repo — live mode no longer requires a phantom serving endpoint

`AgentBricksClient.assess_claims()` is now a **pure mapper** — no model call, no
serving endpoint (the extraction happened upstream in the pipeline).
`available()` now reflects that, and `BackendConfig.mode()` becomes live when a
complete AI Search endpoint/index pair is configured. Tests cover both complete
and partial configurations.

### Blocker #3 — retrieval is not configured, and the SQL path doesn't exist

`.env` has the vector-search variables **commented out**:

```
# AVEN_VECTOR_SEARCH_ENDPOINT=
# AVEN_VECTOR_SEARCH_INDEX=
```

→ `has_vector_search` is False → `retrieve()` returns `None` → demo mode, always.
The index described in `databricks/05_vector_search_setup.md` has (as far as this
review can tell) never been created against the real table.

Meanwhile `.env` advertises a path that **does not exist in the codebase**:

```
# --- SQL warehouse (used by src/backend/sql_search.py) ---
# --- Optional: AI Search. Leave unset to run on SQL retrieval alone. ---
```

There is no `src/backend/sql_search.py`. The SQL warehouse *is* configured and
its credentials work; Vector Search is *not* configured. So the comment has it
exactly backwards relative to what's implemented.

---

## Priority order to finish the product

### P0 — get to a live, judge-proof demo

0. **Check the old workspace for a surviving `facilities_searchable` before
   rebuilding.** If `dbc-7e1b9c30`'s quota has reset and the table is intact,
   copying/reading it is dramatically cheaper than re-running the 10k-row
   `ai_query` pass. Decide this first — it changes everything below it.

1. **Rebuild the derived tables in the new workspace (Blocker #1),** if #0 says
   we must. Order: `extract_data.py` → `database.py`. Before running the
   expensive pass, **fix the final `SELECT` to carry `latitude`, `longitude`,
   `address_city`, `facilityTypeId`, `operatorTypeId`** (Blocker #1b) — getting
   this wrong means paying for the LLM pass twice. Validate `operatorTypeId`
   against `{public, private, government}` and map anything else to unknown
   (Blocker #1c).

2. **Un-gate the mapper (Blocker #2).** ~5 lines in `agent_bricks.py` +
   `config.py::mode()`. Update `test_agent_bricks.py` / any `mode()` test.
   Nothing else can show `live` until this lands.

2. **Land `src/backend/sql_search.py` — retrieval over the warehouse.**
   This is the *reliable* live path: the warehouse credentials already work,
   whereas Vector Search needs an endpoint we have not stood up. Query
   `workspace.default.facilities_searchable` filtered on capability, return rows
   in the same shape `vector_search.retrieve()` returns, so `agent_bricks` and
   `service` need no changes. Must return `None` on any failure.
   - Do **not** reuse root `database.py::build_query` — it is broken (see #10).
   - Wire `service.py` to try Vector Search first, then SQL, then demo.

3. **Create the Vector Search index (rubric points).** The brief explicitly
   rewards Mosaic AI Vector Search and `vector_search.py` is already written
   correctly against Model B. Follow `databricks/05_vector_search_setup.md`
   using the corrected source table (`facilities_searchable`, PK `unique_id`).
   Then set `AVEN_VECTOR_SEARCH_ENDPOINT` / `AVEN_VECTOR_SEARCH_INDEX`.
   Blocked on quota (#1). If Free Edition won't allow the endpoint, #2 carries
   the demo and we say so honestly.

4. **Capture a real-row fixture and prove the pipeline on it.** Pull ~20 real
   rows once, commit as a test fixture, and add an end-to-end test:
   fixture rows → `assess_claims` → `build_shortlist` → display dicts. This is
   what makes the pipeline *demonstrably* real even if the warehouse is
   throttled at judging time, and it's the insurance policy for #1.

5. **Run the golden path end to end with retrieval on** and confirm the UI badge
   flips to "Live Databricks evidence" (`app.py:1005`). Until someone has seen
   that, "live" is a claim, not a fact.

### P1 — makes the demo credible

6. **MLflow 3 dependency and trace seams — done in repo.** Every pipeline stage
   opens bounded spans and the deployment installs MLflow 3. A configured live
   experiment and visible trace remain workspace proof items.

7. **Literal validator — done deterministically.** `agent_bricks` re-verifies
   every extracted span against the preserved raw field and fails closed when a
   row/column receipt cannot be produced. A served model is not needed for this
   safety check.

8. **Native review of the machine-drafted translations.** `localization.py`
   calls them *approved*; they are not. Highest priority: the five
   `emergency_*` keys — machine-drafted safety copy is a real risk, not polish.
   Needs a Hindi and a Marathi speaker. **Still blocked — no native reviewer
   available.** Also still hardcoded English: the login popover, profile page,
   saved-plans, and blocklist screens (`app.py` around `show_account_control`,
   `show_profile`, blocklist/rating captions).

9. **Auth/persistence conflict — resolved in the React path.** The production
   API uses Databricks proxy identity, a pseudonymous owner ID, minimized
   payloads, and owner-scoped Lakebase queries. The legacy Streamlit profile
   adapter is not part of the deployed React path. Live two-user proof remains.

10. **Fix or delete root `database.py`.** `build_query` is broken two ways:
    the quoting is malformed — `"', '".join(...)` interpolated bare produces
    `arrays_overlap(specialties, a', 'b)` — and it calls `arrays_overlap` on
    `procedures`, which is `ARRAY<STRUCT<claim, evidence>>`, not an array of
    strings, so it cannot match. It is not imported by the app. Fold the working
    idea into `sql_search.py` (#2) and delete this, rather than leaving a broken
    query builder that looks usable.

### P2 — if time allows

11. **Lakebase repository wiring — done.** `lakebase.py` now consumes managed
    resource coordinates, generates rotating OAuth DB credentials, validates or
    creates the safe schema, and returns an owner-scoped store. The remaining
    requirement is deployment evidence, not another local profile mirror.
12. **Genie is already done** — `genie.py` is a complete implementation
    (conversation start/continue, SQL + rows extraction, returns `None` on any
    failure). It only needs `AVEN_GENIE_SPACE_ID` set and a Genie space created
    to light up. No code work. *Surface it in the UI* — nothing calls
    `service.ask_data_question()` from `app.py` yet, so a finished feature is
    currently invisible to judges. Cheap win.
13. **Distance/type wiring — done for the golden path.** Coordinates and
    validated operator type now reach ranking; known demo cities use a labelled
    straight-line distance and unknown origins remain `not documented`. Live
    rebuild and city/coordinate conflict review are still required.
14. **Emergency question is not universal.** The intake panel short-circuits on
    its own checkbox and the urgency slider only offers Routine/Soon/Urgent, so
    `urgency == "emergency"` cannot be selected; the `ui_contract` emergency
    branch is a backstop only.
15. **Ratings/blocklist → trust.** Today the blocklist only filters the UI.
    Decide whether "never refer me here" and low ratings feed ranking — kept
    strictly separate from facility evidence so it can never fabricate
    capability.
16. **`vaccination` capability** — present in `demo_adapter.CARE_TASKS` and
    `domain._CARE_TASKS`; confirm the dataset expresses immunization as a
    capability/service string so retrieval can match it.

---

## ✅ Already done (was listed as outstanding in the previous revision)

The old file's P0.2–P0.4 and several P1/P2 items have shipped. Recorded here so
nobody re-does them:

| Item | Status |
|---|---|
| Merge `clara` (`extract_data.py`, `flatten_data.py`, `database.py`) | ✅ merged to `main` |
| `vector_search.retrieve()` — all three Blocker #2 defects | ✅ fixed: correct `databricks.vector_search.client` import, lazy index build in `_get_index()`, no token in config, `try/except → None` |
| `databricks-vectorsearch` in requirements | ✅ uncommented |
| `agent_bricks.assess_claims()` as row → `FacilityCandidate` mapper | ✅ written + tested (`test_agent_bricks.py`) |
| MLflow tracing wired through the pipeline | ✅ code done (spans + inputs/outputs at every stage); ⚠️ dep still commented out — see #6 |
| Genie `ask()` | ✅ fully implemented, not a stub — see #12 |
| Dead `LANDING_COPY` / `tagline` / `promise` / `vitals` strings | ✅ removed |
| Emergency warning + confirmation summary routed through `tx()` | ✅ done |

## ✅ Decision — Model B is the schema of record

`workspace.default.facilities_searchable` (flattened JSON, one row per facility,
key `unique_id`) is the schema of record. Model A (`facilities_normalized` /
`facility_claims_evidence` / `facility_trust_assessment` /
`facility_source_chunks`) is superseded — those tables were never built, and
`src/enrichment.py`'s extractor schema already matches Model B exactly.

- `databricks/01`–`05` are marked superseded in-file; reference only, not
  instructions to run.
- `src/databricks_adapter.py`'s `_FACILITY_QUERY` / `_NEARBY_FACILITY_QUERY` /
  `DatabricksFacilityRepository` are Model A and **not** on the live path
  (`service.py` imports only `SessionLocalPlanStore` / `FallbackPlanStore` from
  it, via `ui_contract.py`). Parked, not deleted: 8 tests cover the
  SQL-building/row-translation logic and it was already dead code on the
  request path.
- ⚠️ The earlier note that Model B "has no `latitude`/`longitude`" was **true of
  the flattened table but false of the source** — the coordinates exist upstream
  and were dropped in flattening. See Blocker #1b and #13.

## Where things live

| Concern | File | Status |
|---|---|---|
| Config from env | `src/backend/config.py` | ✅ Vector Search alone activates live evidence mode |
| Service facade | `src/backend/service.py` | ✅ live path + demo fallback + spans |
| Vector Search | `src/backend/vector_search.py` | ✅ code done; ⛔ index/env not configured |
| SQL retrieval | `src/backend/sql_search.py` | ⛔ **does not exist** — see P0.2 |
| Agent Bricks | `src/backend/agent_bricks.py` | ✅ deterministic raw-receipt validator/mapper |
| Genie | `src/backend/genie.py` | ✅ done; not surfaced in the UI |
| MLflow 3 tracing | `src/backend/tracing.py` | ✅ done; dep commented out |
| Lakebase | `src/backend/lakebase.py` | ✅ secure code path; ⛔ live resource/cross-session proof |
| Domain rules / ranking | `src/domain.py` | ✅ done (pure) |
| Databricks SQL repo | `src/databricks_adapter.py` | 🅿️ Model A, parked, off the live path |
| Seeded demo data | `src/demo_adapter.py` | ✅ fallback |
| UI façade | `src/ui_contract.py` | ✅ sole planning entry point; safety gates run |
| Translations | `src/localization.py` | ⚠️ machine-drafted, unreviewed |
| Trust receipts | `src/trust.py` | ✅ wired via `enrichment.assess_record()` |
| Extractor schema | `src/enrichment.py` | ✅ matches the real table (Model B) |
| Data pipeline | `extract_data.py`, `flatten_data.py` | ✅ on `main`; built the real table |
| Root query builder | `database.py` | ⛔ broken — see #10 |

## Environment variables (set as Databricks App resources)

All optional; blank or `TODO_...` = that tool is treated as unavailable.

```
DATABRICKS_SERVER_HOSTNAME     # SQL warehouse            ✅ set locally, works
DATABRICKS_HTTP_PATH           # SQL warehouse            ✅ set locally, works
AVEN_CATALOG / AVEN_SCHEMA     # Unity Catalog (workspace/default)
AVEN_VECTOR_SEARCH_ENDPOINT    # Mosaic AI Vector Search  ⛔ commented out
AVEN_VECTOR_SEARCH_INDEX       # index over facilities_searchable  ⛔ commented out
AVEN_SERVING_ENDPOINT          # only needed once the Validator (#7) lands
AVEN_GENIE_SPACE_ID            # Genie space              ⛔ unset; code is ready
ENDPOINT_NAME / PGHOST / PGDATABASE / PGUSER  # injected by attached Lakebase resource
AVEN_MLFLOW_EXPERIMENT         # MLflow experiment path   ⛔ unset
```

The root pipeline scripts read `SERVER_HOSTNAME` / `HTTP_PATH` / `ACCESS_TOKEN`
instead — standalone scripts with a PAT, fine for offline table-building, but
they must not become the app's auth path.

## Branch state

| Branch | Contains | Action |
|---|---|---|
| `main` | UI + backend seam + safety gates | — |
| `valval-backend` | current working branch | — |
| `mariam`, `valval`, `valval-pt2`, `clara`, `clara1` | merged ✅ | — |

## Deploy

- App entry: `apps/referral-copilot/run_app.py`; React build entry:
  `apps/referral-copilot/package.json`; deploy config: `app.yaml`.
- Uncomment `mlflow` in `apps/referral-copilot/requirements.txt` (see #6).
  Must run on **Databricks Free Edition** — mind the daily quota (#1).
- Secrets/resources come from the Databricks App, not source. Do not commit
  `.env` or `.aven_profiles.json` (already gitignored).

## Validation

```bash
python -m unittest discover -s apps/referral-copilot/tests
python -m compileall -q apps/referral-copilot
npm test
npm --prefix apps/referral-copilot run build
npm run check:elevenlabs
```
