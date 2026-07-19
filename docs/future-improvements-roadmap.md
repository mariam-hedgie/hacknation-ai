# Aven future improvements and global expansion roadmap

## Why this document exists

This is the durable planning reference for agents expanding Aven after the
current Hack-Nation build. Read it before proposing or implementing a new
language, country, data source, map provider, model provider, authentication
method, cost estimate, or care workflow.

The official Data Legend brief and final submission gate remain authoritative
for the hackathon. A global feature must not displace unfinished challenge
requirements or make a seeded/local capability appear live.

## Priority order

### P0 - finish the India Databricks Referral Copilot

Do not call Aven submission-ready until all of these are proven:

- the organizer's 10,000-row facility dataset is running in Databricks Free
  Edition;
- live retrieval returns literal row-level evidence and visible gaps;
- real facility coordinates produce honestly labelled distance information;
- a user can save a shortlist and reopen it in a new session through Lakebase;
- the deployed Databricks App runs the exact submitted Git commit;
- the evidence, uncertainty, safety, feedback, and owner-isolation gates pass.

Voice, generative intake, polished maps, and extra languages are enhancements.
They do not replace these requirements.

### P1 - harden the India experience

- Live geocoding and route-distance matrix for shortlisted facilities.
- Validated English, Hindi, and Marathi UI and voice journeys.
- Official facility contact discovery with retrieval time and provenance.
- Search or recommendation for a named doctor only when an attributable
  provider roster supports it.
- Sourced consultation/procedure amounts and travel estimates, always separated
  from user-entered budgets and never presented as quotes or guarantees.
- Accessible mobile layout, keyboard navigation, low-bandwidth states, printable
  handoff, and offline-safe emergency guidance.
- Monitoring for broken sources, stale evidence, provider errors, cost, latency,
  and unsuccessful searches.

### P2 - expand by country and language

Expand one jurisdiction at a time. A country launch requires a facility-data
contract, emergency-information owner, privacy review, local clinical/access
reviewer, supported map behavior, currency rules, and a localized evaluation
set. A translated interface alone is not a country launch.

## Global architecture

Keep country-specific behavior behind explicit adapters rather than adding
conditionals throughout the Streamlit UI.

```text
reviewed typed/voice request
  -> locale pack
  -> country policy and emergency adapter
  -> structured intake with user confirmation
  -> jurisdiction facility/evidence adapter
  -> trust and ranking engine
  -> routing and cost adapters
  -> evidence receipt, feedback, and saved action
```

Recommended interfaces:

- `LocalePack`: UI strings, formats, writing direction, voice-language codes,
  fallback language, and reviewer/version metadata.
- `CountryPolicy`: supported care tasks, emergency behavior, consent text,
  currency, units, privacy/retention rules, and prohibited claims.
- `FacilityEvidenceProvider`: source rows, source license, stable record ID,
  retrieved/updated time, literal evidence spans, and missing-field semantics.
- `Geocoder`: typed place or consented coordinates to normalized coordinates,
  with confidence and attribution.
- `RouteProvider`: route distance/duration, supported mode, retrieval time,
  estimate/live label, attribution, and explicit unavailable state.
- `CostProvider`: sourced amount/range, currency, included items, geography,
  source, date, and confidence. It must never silently manufacture a cost.
- `IdentityProvider`: authenticated, pseudonymous owner identity; Google or
  other social login must map to the same owner-isolation contract.
- `VoiceProvider`: audio to reviewable transcript. Voice never bypasses the
  editable confirmation step.

Every provider must have a deterministic fallback, timeout, safe error state,
and user-visible truth label. Secrets stay server-side.

## Language roadmap

### Existing launch languages

- English
- Hindi
- Marathi

These are not considered complete merely because string keys exist. Each needs
native-speaker review of the full golden path, emergency wording, evidence
status, budget/currency copy, form validation, and voice transcription.

### Candidate India expansion

Evaluate Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, and
Urdu next. This is a candidate list, not a commitment or claim of coverage.
Prioritize using intended-user demand, facility-data geography, reviewer
availability, voice accuracy, and demo/product value.

### Candidate global expansion

Choose the first non-India market only after P0 and P1. Use a scored decision:

| Factor | Required evidence |
|---|---|
| User need | Named coordinator/patient workflow and partner or user research |
| Facility data | Legal, attributable, maintainable source with stable IDs |
| Language quality | Qualified reviewer and tested voice/text support |
| Safety | Local emergency and healthcare-access review |
| Routing | Provider coverage for relevant modes and geography |
| Privacy | Documented consent, retention, and cross-border data handling |
| Buildability | One complete, testable vertical slice |

Spanish, Portuguese, French, Arabic, and Indonesian are reasonable discovery
candidates because they can unlock multiple regions, but no language should be
added before selecting a specific country, user, evidence source, and reviewer.

### Localization rules

- Keep canonical internal enums language-neutral; translate display labels only.
- Render the public brand as `Aven` plus a reviewed native-script rendering
  where appropriate. Do not transliterate automatically and call it translated.
- Never machine-translate a literal evidence receipt without also preserving
  the original text and clearly labelling the translation.
- Support right-to-left layout before launching Arabic or Urdu.
- Localize pluralization, dates, numbers, distance units, currency, addresses,
  telephone formats, names, and accessibility copy—not only button labels.
- Translate emergency and consent language through human review.
- Use fallback chains such as `mr-IN -> mr -> en`, and display a notice when a
  fallback is used.
- Version locale packs and record reviewer, review date, and tested release.

## Maps, GPS, and routing alternatives

Browser GPS and route calculation are separate capabilities. Browser location
requires explicit user permission and an HTTPS-capable client integration.
Coordinates then go through a route provider; an API key alone does not capture
the user's location.

Provider candidates:

| Provider | Best fit | Important boundary |
|---|---|---|
| Google Maps Platform | Broad geocoding, Places, routes, and transit evaluation | Requires enabled APIs, billing, quotas, and restricted keys |
| Mapbox | Custom global map UI, directions, and distance/time matrices | Check country coverage, token restrictions, limits, and pricing |
| openrouteservice + OpenStreetMap | Open-data road routing fallback and self-hosting path | Hosted quotas apply; public services are not a guaranteed production backend |
| HERE | Enterprise/global routing candidate | Validate country/mode coverage, licensing, and current terms before selection |
| Offline comparison | Demo and outage fallback | Must say comparison only; never claim live route, traffic, fare, or transit |

Primary references:

- Google Routes API: <https://developers.google.com/maps/documentation/routes/reference/rest>
- Mapbox Directions: <https://docs.mapbox.com/api/navigation/directions/>
- Mapbox Matrix: <https://docs.mapbox.com/api/navigation/matrix/>
- openrouteservice API: <https://openrouteservice.org/dev/>

Required route result fields are provider, origin/destination provenance,
mode, distance, duration, retrieval time, live-versus-estimate label, and
attribution. Taxi, public-transit, flight, lodging, traffic, and fare claims
need separate supported sources.

## AI, NLP, and voice alternatives

Databricks remains the evidence, trust, retrieval, and persistence center for
the challenge build. A general model may improve intake extraction or question
selection, but it must not invent facility capabilities or become the hidden
source of the ranking.

Possible roles:

- OpenAI Responses API: structured multilingual intake, clarification, and tool
  orchestration with a strict schema and reviewed output.
- Databricks model serving/Agent Bricks: sponsor-aligned claim extraction,
  evidence reasoning, and trust workflow over the supplied records.
- ElevenLabs Scribe: explicit recorded voice intake returned as editable text.
- Alternative speech providers: OpenAI audio, Google Cloud Speech-to-Text,
  Azure AI Speech, or AWS Transcribe, selected per tested language, privacy,
  residency, latency, and cost—not brand preference.
- On-device speech or text models: future privacy/low-connectivity option after
  measuring device coverage and quality.

For every model/provider, record model/version, prompt/schema, consent,
submitted fields, region/retention settings, latency, cost, errors, and fallback.
Do not send raw health narratives to web-search or unrelated enrichment tools.

## Healthcare data and global evidence

Each country needs a source registry containing:

- official or licensed facility source and governing organization;
- license and permitted reuse;
- stable facility/organization identifiers;
- refresh cadence and last successful retrieval;
- fields that are claims versus independently verified facts;
- source language and permitted translation behavior;
- geographic coverage and known missingness;
- correction, takedown, and source-conflict process.

Public web discovery may find contact pages, fee schedules, or provider rosters,
but search results are candidates, not verified evidence. Prefer government,
regulator, facility, payer, or recognized directory sources. Store the source
URL and retrieval time, preserve the supported text, and lower confidence or
return unknown when sources conflict.

## Emergency and clinical-safety localization

- Do not hard-code one emergency number as globally correct.
- Determine emergency copy from an authoritative country/region source and
  version it separately from general translations.
- Always allow manual region correction when GPS or locale inference is wrong.
- Emergency UI must work without login, AI, voice, maps, or Databricks.
- Aven remains care-access decision support: no diagnosis, triage score,
  medication change, eligibility decision, or treatment promise.
- Record when emergency guidance was shown, but do not persist the user's raw
  symptom narrative.

## Currency, prices, and affordability

- Keep travel budget and care budget separate.
- Store money as amount plus ISO currency; format it using the selected locale.
- Label every displayed cost as user-entered, documented, externally estimated,
  or unknown.
- Include source, date, geography, inclusions/exclusions, and range assumptions.
- Never convert a price without recording exchange-rate source and timestamp.
- Do not imply insurance/benefit eligibility or a guaranteed final bill.
- If no attributable amount exists, show `not confirmed` and provide the next
  verification action.

## Authentication and saved plans

Databricks OAuth is the challenge deployment identity. Future Google, Apple,
Microsoft, phone, or passwordless login is permitted only behind the same
server-validated pseudonymous owner contract. Social login does not change
evidence or recommendation behavior.

Before enabling a new identity provider, test account linking, duplicate
accounts, logout, deletion, recovery, revoked access, two-user isolation,
session expiry, and consent. Never place provider client secrets in browser code.

## Accessibility and low-connectivity roadmap

- WCAG-oriented contrast, focus, keyboard, labels, errors, and screen-reader
  testing.
- Reduced-motion and text-size support.
- Right-to-left and long-string layout testing.
- Low-bandwidth mode without map tiles or automatic voice downloads.
- Printable/shareable text plan with evidence and unknowns.
- Clear offline state and retry without losing reviewed input.
- Voice is optional; every voice action has an equivalent typed path.

## Evaluation required before release

Maintain at least 5-10 cases per supported country/language, including:

- strong literal evidence;
- unsupported claim;
- conflicting evidence;
- missing doctor/capacity/cost information;
- rural or sparse-data location;
- invalid or denied GPS;
- provider timeout/rate limit;
- voice mistranscription and manual correction;
- emergency interruption;
- save, sign out, sign in, and reopen;
- right-to-left or long-translation layout when relevant.

Measure extraction accuracy, evidence-span validity, unsupported-claim rate,
ranking stability, source freshness, route availability, translation review,
task completion, correction rate, accessibility, latency, and cost. Never invent
scores or call an unreviewed case a validated result.

## Trusted workflow checkpoint for every future feature

Before implementation, the proposing agent must document and ask the user to
confirm or adjust:

- **Trace:** input, structured output, sources/tools, confidence, provider/model
  version, retrieval time, and final user action.
- **Feedback:** helpful/incorrect control and how the correction is retained
  without rewriting immutable source evidence.
- **Evaluation:** seeded cases covering accuracy, evidence, safety, usefulness,
  localization, failure, and actionability.
- **Guardrail:** explanation, uncertainty label, safe fallback, and user approval
  before consequential search, ranking, sharing, or saving.

## Future-agent change protocol

1. Read `AGENTS.md`, the official challenge PDF, the final submission gate,
   this roadmap, and the closest architecture/security document.
2. State whether the change is P0, P1, or P2 and why it does not displace a
   higher-priority blocker.
3. Verify provider capabilities and terms from current primary documentation.
4. Write tests before production code for the new adapter, truth label,
   fallback, localization, and privacy boundary.
5. Never add a secret or real patient/facility dataset to Git.
6. Demonstrate the capability with a real safe request, then record what was
   locally tested versus live/deployed.
7. Update this document when a provider, country, language, reviewer, or product
   decision is confirmed. Move ideas from `candidate` to `supported` only with
   dated evidence.

## Decision record template

```text
Decision:
Date / owner:
Priority: P0 | P1 | P2
Country / language:
Named user and problem:
Provider or source:
Primary documentation checked:
Data/privacy review:
Trace / feedback / evaluation / guardrail:
Fallback:
Local test evidence:
Live/deployment evidence:
Remaining limitations:
```
