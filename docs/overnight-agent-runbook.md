# Aven: 15-hour overnight agent runbook

## Locked product decisions

- **Public product name:** Aven
- **Track / mission:** Databricks Data Legend - Referral Copilot
- **Demo languages:** English, Hindi, Marathi
- **Demo settings:** Patna/Bihar long-distance access; Delhi, Bengaluru, and
  Mumbai urban tradeoff examples
- **Core promise:** a person explains their care-access need naturally; Aven
  confirms the request, gives actionable next steps, exposes evidence/unknowns,
  and saves the plan.

## Mapping decision

### Recommended live mode: Google Maps Platform, strictly capped

Use Google only for **Routes, Places, Geocoding/Autocomplete, and map display**.
It is the only proposed option that can cover driving, walking, bicycle,
motorbike, and public transit (including bus/train when coverage exists) through
one supported routing layer. Set API quotas and budget alerts before adding the
key. Do not enable unbounded usage. Google Maps Platform is pay-as-you-go with
per-SKU free usage caps; check the current console pricing before demo use.

Required APIs:

```text
Maps JavaScript API or Maps Embed API
Routes API
Places API (New)
Geocoding API / Autocomplete
```

Key rules:

- Store `GOOGLE_MAPS_API_KEY` only as a Databricks App secret or local ignored
  `.env`; never commit or paste it into chat.
- Restrict the key to required APIs, expected app URL/referrers or server IP,
  and small daily request quotas.
- Cache a route response per confirmed saved plan; never recompute on every UI
  rerender.
- Ask GPS permission only after the user chooses `Use my location`; always
  support typed city/address input.

### Free fallback mode: visual map + road-only routing

If a Google billing account/key is unavailable, use:

```text
MapLibre GL JS + OpenStreetMap attribution for the visual map
openrouteservice for car, walking, bicycle, and road-distance estimates
Google Maps directions link for user-initiated external transit navigation
```

This fallback is suitable for the demo but **does not** supply reliable public
transit, motorbike, taxi, flight, hotel availability, or live price data. It
must label those as `check in Maps` or `not confirmed`.

Openrouteservice's free standard tier currently lists a daily Directions limit,
and requires attribution; use it only behind the backend and cache results.
Do not use the public Nominatim endpoint for autocomplete or high-volume
geocoding; its public policy limits use to one request/second and requires a
valid identifying user agent/referer.

## Feature truth table

| Requested feature | Build now | Live data source | Required product label |
|---|---|---|---|
| Typed/GPS location | Yes | Browser GPS + geocoding | `Location from you` |
| Walk/car/cycle/motorbike route | Yes | Google Routes; ORS fallback for road modes | `Estimated route` |
| Bus/train | Yes, conditional | Google transit route when available | `Transit estimate - verify service` |
| Taxi | Link-out only | Driving duration + external Maps link | `Taxi fare/availability not confirmed` |
| Plane | Demo-only long-distance flag | No live flight API | `Air travel may be needed - not priced` |
| Lodging near facility | Yes, conditional | Google Places lodging search | `Nearby lodging - availability/rate not confirmed` |
| Facility appointment | Yes, conditional | Dataset/official facility source | `Official contact/link` or `Call to confirm` |
| Busy/optimal time | Opening hours only | Official source / Places opening-hours field | Never claim crowd levels |
| Cost | Yes, conditional | Official published fee only | `Price not confirmed` when absent |
| Subsidized/public route | Yes, conditional | Facility type + official scheme link | Never decide eligibility |
| Pharmacy/refill | Task flow and nearby finder | Dataset/Places when available | Never claim stock or prescribe |
| Lab/blood draw | Task flow and facility finder | Dataset/official lab source | Only source-backed preparation info |
| Voice / 3 languages | Yes | ElevenLabs backend integration | User reviews extracted text |
| Evidence / uncertainty | Yes, required | Databricks derived tables | `Why this option?` |

## Team/agent deployment model

Work in waves so agents do not overwrite each other. The orchestrator owns
integration, scope, tests, and final demo. Every agent must read `AGENTS.md`,
the original challenge PDF, and the task-specific handoff before coding.

### Wave 1: build independently (hours 0-4)

| Agent | Owns | Inputs | Must return |
|---|---|---|---|
| Databricks team (external) | Raw/derived tables, trust contract, Lakebase, App resources | `docs/databricks-team-handoff.md` | Table names, schema, sample response, App URL/resource keys |
| Aven app agent | Conversational UI, confirmation, action plan, Evidence Receipt, save/share flows | `docs/final-product-plan.md` | Local Streamlit screen flow with demo adapter |
| Domain/safety agent | Intake schema, emergency/refill/lab guardrails, ranking and evidence rules | final plan + seeded cases | Pure tested functions and fixtures |
| Maps/access agent | Map provider adapter, mode comparison cards, provider quota/cache policy | this document | Provider interface + demo fixture and no-key fallback |

### Wave 2: integrate (hours 4-8)

| Agent | Owns | Done when |
|---|---|---|
| Data adapter agent | Replace demo adapter with Databricks SQL/Lakebase adapter | App can query a documented table contract without exposing credentials |
| Voice/language agent | ElevenLabs voice input/read-back; English/Hindi/Marathi prompts | Text confirmation remains mandatory and text-only path still works |
| UX/plan agent | Make plain-language action plan, travel/lodging/checklist views | A user can act without opening technical evidence |
| QA agent | Seeded test matrix | Documented, conflicting, unknown, emergency, refill, lab, save/reload all pass |

### Wave 3: integrate and harden (hours 8-12)

The orchestrator merges only after all contracts match:

```text
confirmed intake
  -> get_shortlist(request)
  -> option cards + evidence receipt + route comparison
  -> save_plan(plan, note)
  -> reload_plan(plan_id)
```

Required integration tests:

1. Patna referral: long travel, public preference, price unknown.
2. Delhi: nearby versus stronger evidence tradeoff.
3. Bengaluru: transit versus convenience tradeoff.
4. Mumbai: facility option plus nearby lodging card, clearly not a reservation.
5. Symptom-first emergency warning: normal ranking stops.
6. Refill: prescription context required; no stock/dose claims.
7. Save note/override, reload, reopen.

### Wave 4: deploy and demo (hours 12-15)

1. Push the known-good Git commit.
2. Databricks owner deploys that exact commit to the custom App.
3. Attach SQL warehouse, Unity Catalog tables, Lakebase, and optional secrets.
4. Test fresh App URL in a separate browser session.
5. Keep a no-key deterministic demo path enabled.
6. Record a backup demo video and submit only after the deployed path works.

## Mandatory handoffs

### Databricks -> app team

```text
catalog/schema/table names
SQL warehouse resource key
Lakebase resource key
shortlist query input/output shape
one documented case, one conflicting case, one unknown case
known unsupported fields
```

### App team -> Databricks

```text
apps/referral-copilot source path
requirements.txt and app.yaml
required resource list
environment variable names only (never secret values)
expected save/reload API/table contract
final Git commit SHA
```

### Product/QA -> everyone

```text
approved action-plan wording in three languages
emergency/refill/lab boundaries
seeded scenario expected outputs
demo script and fallback screens
```

## Agent guardrails

- No agent commits raw challenge data, patient data, credentials, or secret
  values.
- No one invents costs, eligibility, availability, stock, clinical outcomes,
  reviews-as-quality, diagnoses, or busy-time data.
- All source-backed facility claims require a literal evidence span.
- External Maps/Places data is supplementary and visibly separated from
  challenge-dataset evidence.
- Live integrations can enhance the demo, but the seeded route/evidence
  scenario must still work when an API fails.

## Definition of done at hour 15

The deployed Databricks App demonstrates one spoken or typed Aven request in
English, Hindi, or Marathi; confirmation before search; a three-option
evidence-backed care plan; route/travel information with honest labels; one
save/reload action; and an Evidence Receipt showing both proof and unknowns.
