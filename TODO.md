# Aven — Integration TODO

Track: **Referral Copilot** (Data Legend / Databricks challenge).

State of play: the frontend is complete and green (136 tests, 214 subtests pass on
`main`). The backend seam exists and every external integration is a stub that
falls back to seeded demo data, so the app runs today. Real Databricks tables
exist — but they were built on `clara`, against a **different schema** than the
one `main`'s adapters assume. Reconciling that is the critical path.

The frontend calls **only** `apps/referral-copilot/src/backend/service.py`. Never
call a Databricks tool from `app.py` directly.

---

## ✅ Decision — Model B adopted (2026-07-19)

Model B (flattened JSON, `workspace.default.facilities_searchable`) is the
schema of record. Model A (`facilities_normalized` / `facility_claims_evidence`
/ `facility_trust_assessment` / `facility_source_chunks`) is superseded: those
tables were never built, and `src/enrichment.py`'s extractor schema already
matches Model B exactly.

Consequences applied:

- `databricks/01`–`05` are marked superseded in-file (see each file's header).
  They document a pipeline against tables that don't exist; kept for reference
  only, not as instructions to run.
- `src/databricks_adapter.py`'s `_FACILITY_QUERY` / `_NEARBY_FACILITY_QUERY` /
  `DatabricksFacilityRepository` are Model A and are **not** on the live path
  (`service.py` never imports them — only `SessionLocalPlanStore` /
  `FallbackPlanStore` from this module are used, via `ui_contract.py`). Parked
  rather than deleted: 8 existing tests cover the SQL-building/row-translation
  logic and deleting it would be a pure regression for zero behavior change,
  since it was already dead code on the request path.
- No `latitude`/`longitude` in `facilities_searchable` — distance ranking has
  no source. Shipping with `distance_km = None` (UI already handles this
  honestly); geocoding stays P2 (#12), blocked until coords exist.

---

## ⚠️ Blocker #1 — two competing data models (historical — resolved above)

There are two incompatible facility schemas in this repo, and nothing on `main`
can read the data that actually exists.

| | **Model A — evidence tables** (`main`, `databricks/`) | **Model B — flattened JSON** (`clara`) |
|---|---|---|
| Tables | `facilities_normalized`, `facility_claims_evidence`, `facility_trust_assessment`, `facility_source_chunks` | `workspace.default.facilities_searchable` |
| Grain | one row per **claim/evidence span** | one row per **facility** |
| Key | `facility_id` / `source_row_id` | `unique_id` |
| Columns | `capability`, `literal_source_text`, `cited_span`, `source_column`, `lat`, `lon` | `name`, `specialties[]`, `capabilities[]`, `procedures[]`, `equipment[]`, `facility_facts[]`, `data_quality` |
| Built? | **No** — scripts exist, never run against real data | **Yes** — `flatten_data.py` created it from the Databricks dataset |
| Read by | `databricks_adapter.py::_FACILITY_QUERY` | `clara1`'s `vector_search.py` |

**Recommendation: adopt Model B.** It is the one with real rows in it, and — this
is the important part — `src/enrichment.py`'s documented extractor output schema
**already matches Model B exactly** (`capabilities`/`procedures`/`equipment` as
`{claim, evidence[]}`, plus `specialties`, `facility_facts`, `data_quality` with
`conflicting_claims` / `possible_merged_facility` / `merge_suspicion_reason`).
The contract everyone was waiting on is, in effect, already agreed — it was just
never written down in the same place twice.

Consequences of adopting B:

- `databricks_adapter.py`'s two queries become dead code. Keep the module for
  `SessionLocalPlanStore` / `FallbackPlanStore`, delete or park the SQL.
- `databricks/01`–`04` + `05_vector_search_setup.md` describe Model A. Either
  rewrite them for B or mark them superseded — right now `05` tells you to index
  `facility_source_chunks`, which does not exist.
- **No `latitude`/`longitude` in `facilities_searchable`.** Distance ranking has
  no source. Either add coords to the table or ship with distance honestly
  undocumented (the UI already handles `distance_km = None`).

---

## ⚠️ Blocker #2 — `clara1`'s vector_search will crash the app

`origin/clara1` (85990e8) is the only real retrieval code written, and it is the
right idea, but it cannot merge as-is. Three defects:

1. **Wrong import.** `from databricks.ai_search import VectorSearchClient` — the
   package is `databricks-vectorsearch`, module `databricks.vector_search.client`.
   It is also still commented out in `requirements.txt`.
2. **Config fields that don't exist.** Uses `config.workspace_url` and
   `config.databricks_token`; `BackendConfig` has neither, **by design** — its
   docstring states secrets are not read there because the Databricks App
   identity authorizes calls. Adding a PAT would regress that decision.
3. **Client built in `__init__`.** `service.py` instantiates
   `VectorSearchClient(_CONFIG)` at module import, so any connection failure
   takes down the entire app — including demo mode. The whole fallback design
   dies here.

Fix: build the index lazily inside `retrieve()`, wrap in `try/except` → `return
None`, and authenticate via the app identity (no token in config).

---

## ⚠️ Finding — Agent Bricks is much smaller than the old TODO claimed

The old TODO scoped `agent_bricks.assess_claims()` as "call a serving endpoint to
extract claims and literal spans." **That extraction already happened upstream** —
it is baked into `consolidated_json` and parsed out by `flatten_data.py`. Rows
arrive with claims and evidence spans attached.

So `assess_claims` collapses from an LLM integration into a **pure mapper**:

```
searchable row  →  enrichment.normalize(row)
                →  pick the claim group matching the requested capability
                →  domain.evidence_status(span, has_conflict=..., ...)
                →  FacilityCandidate(facility_id=unique_id, display_name=name, ...)
                →  missing_fields for every group that came back empty
```

~60 lines, pure, fully unit-testable, no endpoint required.
`service._live_plan_routes` already ranks and renders whatever it returns.
**This is the highest-value remaining task and it is far cheaper than it looks.**

Still genuinely needed from a model, if time allows: the **Validator** step —
re-verifying an extracted span against the facility's raw record. Nothing does
this today (documented as a known limit in `enrichment._claim_evidence`), and it
is brief stretch #2.

---

## Where things live

| Concern | File | Status |
|---|---|---|
| Config from env | `src/backend/config.py` | ✅ reads env, treats `TODO_...` as unset |
| Service facade | `src/backend/service.py` | ✅ live path written, falls back to demo |
| Vector Search | `src/backend/vector_search.py` | ⛔ stub on `main`; draft on `clara1`, see Blocker #2 |
| Agent Bricks | `src/backend/agent_bricks.py` | ⛔ stub → becomes a mapper, see above |
| Genie | `src/backend/genie.py` | ⛔ stub → returns `None` |
| MLflow 3 tracing | `src/backend/tracing.py` | ✅ no-op until configured |
| Lakebase | `src/backend/lakebase.py` | ✅ local-JSON fallback |
| Domain rules / ranking | `src/domain.py` | ✅ done (pure) |
| Databricks SQL repo | `src/databricks_adapter.py` | ⚠️ queries Model A tables that don't exist |
| Seeded demo data | `src/demo_adapter.py` | ✅ fallback |
| UI façade | `src/ui_contract.py` | ✅ sole planning entry point; safety gates run |
| Translations | `src/localization.py` | ⚠️ 21 keys; 15 machine-drafted, unreviewed |
| Trust receipts | `src/trust.py` | ✅ wired via `enrichment.assess_record()` |
| Extractor schema | `src/enrichment.py` | ✅ matches the real table (Model B) |
| Data pipeline | `clara`: `extract_data.py`, `flatten_data.py`, `database.py` | ✅ built the real table; unmerged |

## Environment variables (set as Databricks App resources)

All optional; blank or `TODO_...` = that tool is treated as unavailable.

```
DATABRICKS_SERVER_HOSTNAME     # SQL warehouse
DATABRICKS_HTTP_PATH           # SQL warehouse
AVEN_CATALOG / AVEN_SCHEMA     # Unity Catalog location (clara used workspace/default)
AVEN_VECTOR_SEARCH_ENDPOINT    # Mosaic AI Vector Search endpoint
AVEN_VECTOR_SEARCH_INDEX       # index over facilities_searchable
AVEN_SERVING_ENDPOINT          # Agent Bricks / FM serving endpoint
AVEN_GENIE_SPACE_ID            # Genie space over the facility tables
AVEN_LAKEBASE_URL              # Lakebase Postgres connection
AVEN_MLFLOW_EXPERIMENT         # MLflow experiment path
```

Note `clara`'s scripts read `SERVER_HOSTNAME` / `HTTP_PATH` / `ACCESS_TOKEN`
instead — standalone scripts with a PAT, fine for offline table-building, but they
must not become the app's auth path.

`service.backend_mode()` returns `"live"` once Vector Search **and** Agent Bricks
are configured; otherwise `"demo"` (the UI shows an honest banner).

---

## Priority order to finish the product

**P0 — the demo-critical path (live data end to end)**

1. **Decide Model A vs Model B** (recommend B). Write the chosen schema down once,
   here, and delete the loser. Everything below is blocked on this.
2. **Merge `clara`** so `extract_data.py` / `flatten_data.py` / `database.py` are on
   `main` and the pipeline that produced the table is reproducible.
3. **Land `vector_search.retrieve()`** — take `clara1`'s query shape, fix the three
   defects in Blocker #2, uncomment `databricks-vectorsearch` in `requirements.txt`.
   Must return `None` on any failure.
4. **Land `agent_bricks.assess_claims()`** as the row → `FacilityCandidate` mapper
   described above, with unit tests over a couple of captured real rows. After 3+4,
   `backend_mode()` reports `live` and the pipeline is real end to end.

**P1 — makes the demo credible**

5. **MLflow 3 tracing** (`tracing.py`) — attach inputs/outputs + token-cost
   attributes per span so extraction → scoring → ranking shows **with receipts**
   (brief stretch #1). Cheap, and it is explicitly rewarded by the rubric.
6. **Native review of the machine-drafted translations (now 17 keys, was 15).**
   `localization.py` is called *approved* translations and they are not
   approved. Highest priority: the five `emergency_*` keys (2 more were added
   2026-07-19 — see #7 — to stop `show_intake()`'s emergency warning/checkbox
   from hardcoding English) — machine-drafted safety copy is a real risk, not a
   polish item. Needs a Hindi and a Marathi speaker. **Still blocked — no
   native reviewer available in this session.**
7. **Language picker gap, corrected and partly closed (2026-07-19).** This item
   was stale: `LANDING_COPY` doesn't exist (landing hero/about/tiles copy is in
   `UI_COPY` and was already fully translated for hi/mr), and most of
   `show_intake()` already used `tx()`. What was actually true and is now
   fixed: `STRINGS["tagline"]`/`["promise"]`/`["vitals"]` were dead (duplicated
   the already-rendered `hero_tagline`/`hero_sub`, "vitals" had no render slot)
   — removed rather than given a new UI slot. The emergency intake warning +
   checkbox in `show_intake()` were hardcoded English — now routed through
   `safety_copy()` via two new governed keys (see #6). The confirmation
   summary sentence and its caption/"See all fields" label were also
   hardcoded English — now `tx("confirm_summary"/"confirm_caption"/
   "confirm_see_fields")`.
   **Still open:** the login popover, profile page, saved-plans, and blocklist
   screens still hardcode English (`app.py` around `show_account_control`,
   `show_profile`, blocklist/rating captions) — not touched this pass because
   it is a large batch of new machine-drafted strings and #6's native-review
   blocker applies to every one of them.
8. **Resolve the auth/persistence conflict.** `mariam`'s `auth.py` (pseudonymous
   owner ID, never stores email) vs `app.py`'s `do_login` (stores name + email) vs
   `SessionLocalPlanStore` vs `src/profiles.py`. See
   `docs/security/login-and-persistence-audit.md`. **Team decision needed** — this
   is the one item nobody can unblock alone.

**P2 — if time allows**

9. **Lakebase** — UPSERT/read profile (history, saved referrals, ratings,
   blocklist) keyed by identity; keep local JSON as an offline mirror.
10. **Validator / self-correction** — re-verify each span against the raw record
    inside `agent_bricks` (brief stretch #2).
11. **Genie** (`genie.py::ask()`) — NL → governed SQL for planner questions;
    surface the generated SQL as part of the evidence trail.
12. **Geocoding / distance** — blocked on coords existing (see Blocker #1).
13. **Emergency question is not universal.** The intake panel short-circuits on its
    own checkbox and the urgency slider only offers Routine/Soon/Urgent, so
    `urgency == "emergency"` cannot be selected; the `ui_contract` emergency branch
    is a backstop only.
14. **Ratings/blocklist → trust.** Today the blocklist only filters the UI. Decide
    whether "never refer me here" and low ratings feed ranking — kept strictly
    separate from facility evidence so it can never fabricate capability.
15. **`vaccination` capability** — added to `demo_adapter.CARE_TASKS` and
    `domain._CARE_TASKS`; confirm the dataset expresses immunization as a
    capability/service string so retrieval can match it.

---

## Branch state

| Branch | Contains | Action |
|---|---|---|
| `main` | UI + backend seam + safety gates, all tests green | — |
| `mariam` | merged ✅ | — |
| `valval`, `valval-pt2` | merged ✅ | — |
| `clara` | `extract_data.py`, `flatten_data.py`, `database.py` — built the real table | **merge (P0.2)** |
| `clara1` | `vector_search.py` draft | **fix, then merge (P0.3)** |

## Deploy

- App entry: `apps/referral-copilot/app.py`; deploy config: `app.yaml`.
- Uncomment deps in `apps/referral-copilot/requirements.txt` (mlflow,
  databricks-vectorsearch) as each integration lands. Must run on **Databricks
  Free Edition**.
- Secrets/resources come from the Databricks App, not source. Do not commit `.env`
  or `.aven_profiles.json` (already gitignored).
