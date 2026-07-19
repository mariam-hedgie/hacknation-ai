# aven

**The right care route, with proof.**

Aven is the Hack-Nation Data Legend Referral Copilot. A person describes a
care-access need in natural language, reviews the structured request, and gets
an actionable facility plan whose evidence and unknowns remain visible. Aven
does not diagnose, prescribe, determine benefit eligibility, or promise price,
stock, availability, outcomes, or crowd levels.

The current repository contains a deterministic local vertical slice plus
live, review-gated OpenAI intake structuring, ElevenLabs transcription, and
Tavily public-source discovery when their server-side keys are configured.
The seeded path stays usable when live services are unavailable.

## Golden-path demo

1. Enter a typed request in English, Hindi, or Marathi.
2. Choose the task: referral/procedure, refill, lab, symptom-first, or follow-up.
3. Set urgency, maximum distance, usable transport modes, separate travel and
   care budgets in rupees, required-arrival date, and public/private preference.
4. Review and confirm Aven's structured interpretation.
5. Compare three clearly labelled options, inspect proof and unknowns, and save
   a choice or correction.

Use the Patna/Bihar case for a long-distance public-care story. Delhi,
Bengaluru, and Mumbai are the planned urban comparison cases.

## Run locally

One-time setup, from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python3 -m pip install -r apps/referral-copilot/requirements.txt
cp .env.example .env
```

Leave unavailable credentials as `TODO_...`; Aven will use safe local fallback
behavior. Never commit `.env` or a Databricks personal access token.

### Start the React app

```bash
source .venv/bin/activate            # Windows: .venv\Scripts\activate
cd apps/referral-copilot
npm install
npm run build
AVEN_AUTH_MODE=local_demo AVEN_ALLOW_LOCAL_DEMO=true python run_app.py
```

Open **<http://localhost:8010>**. The production-shaped local server hosts both
the built React UI and `/api/*` routes on the same origin. Local saved decisions
are deliberately process-local and labelled `local demo`; only a deployed app
with authenticated Lakebase may claim cross-session persistence. For live UI
editing, run `npm --workspace frontend run dev` in a second terminal.

### Run validation

```bash
cd /path/to/hacknation-ai
python3 -m unittest discover -s apps/referral-copilot/tests -v
python3 -m compileall -q apps/referral-copilot
npm test
npm --prefix apps/referral-copilot run build
npm --prefix apps/referral-copilot --workspace frontend run lint
npm run check:elevenlabs
```

The ElevenLabs check reports configuration only; it does not print the key.

If `ELEVENLABS_API_KEY` is configured, the intake offers recording and asks
for explicit consent before sending audio to ElevenLabs. The transcript is
always returned as editable text for review. If `TAVILY_API_KEY` is configured,
each result can search for public doctor, fee, contact, and official-source
candidates. Aven sends only the facility name and confirmed service—not the
patient narrative or location—and search results do not alter the ranking.

### Configure OpenAI, ElevenLabs, and Tavily

Put keys only in the repository-root `.env`; never paste them into the UI or
commit them. Restart the API server after changing `.env`.

```dotenv
OPENAI_API_KEY=your_real_openai_key
OPENAI_MODEL=gpt-5.6-sol
ELEVENLABS_API_KEY=your_real_elevenlabs_key
TAVILY_API_KEY=your_real_tavily_key
```

- **OpenAI:** “Structure with OpenAI” sends only the text in the intake box.
  It returns a draft; the person must review and confirm every extracted field
  before Aven searches or ranks. Aven does not send the model response history
  to OpenAI storage (`store=False`).
- **ElevenLabs:** create a restricted server key with Speech-to-Text access in
  the ElevenLabs dashboard. The recording is sent only after explicit consent,
  and the transcript returns to the editable intake box. Voice is intentionally
  hidden for the hackathon unless `AVEN_VOICE_ENABLED=true`; typed English,
  Hindi, and Marathi remain the reliable path.
- **Tavily:** create a key at <https://app.tavily.com>, add it as
  `TAVILY_API_KEY`, restart the app, open a result, then choose **Contact,
  phone, doctors, fees and public sources → Find contact & public sources**.
  Aven sends only the facility name and confirmed service. It shows the source
  link plus phone candidates found in the snippet; the user must verify a
  number on the linked page before calling.

### Accounts and saved plans

- **Local demo:** no custom account. Saved decisions are process-local,
  disposable, and visibly labelled as such.
- **Databricks workspace account:** the deployed app uses Databricks OAuth proxy
  identity. The server converts that identity to a pseudonymous owner ID and
  scopes every Lakebase query to it; the browser cannot provide an owner ID.
- **Google/Aven sign-in:** not implemented and not needed for the challenge.

Open **My plans** in the top navigation at any time. Durable records retain
only the chosen option, next action, override, and optional note. Health intake,
location, medication, voice, and transcript are not persisted.

### No-key journey and ambulance demo

Every facility card builds a universal Google Maps Directions URL from the
entered origin and hospital name. Google documents that Maps URLs do not need
an API key. The user must verify the exact hospital branch in Google Maps,
because the challenge data does not contain structured addresses, Place IDs,
or coordinates.

The local golden path uses clearly labelled seeded distances, journey times,
and rupee ranges so the complete interaction remains demoable without claiming
live traffic or fares. Bus links open redBus, train links open IRCTC, and flight
links open Air India and IndiGo. These are external booking actions; Aven does
not process a booking or payment and does not claim that a matching service is
available.

Ambulance service is never assumed. Each facility prompts for an ambulance
plan. A documented ambulance claim is shown with its evidence; otherwise Aven
instructs the person to call the hospital and verify. Tavily phone numbers stay
labelled as candidates until checked on their linked source. Seeded ambulance
time/cost ranges are comparisons only, explicitly noting that a hospital or
public ambulance may be free. Emergencies expose the official India `112`
action and bypass ordinary planning.

The recommendation pipeline is intentionally explainable rather than an opaque
LLM verdict:

1. require documented or officially corroborated capability evidence;
2. prefer plans that can plausibly meet the requested arrival date;
3. compare evidence quality, journey time, sourced/seeded travel cost, and the
   user's stated preferences;
4. label missing information as unknown and show every ordering reason.

## Deploy the submission

The challenge submission must be the React + FastAPI build running as a live
Databricks App in Free Edition. Give the Databricks owner the copy-paste
[`deployment handoff`](docs/databricks-team-handoff.md). It covers the exact
resource keys, corrected searchable-table pipeline, AI Search, secret-backed
identity, Lakebase persistence, deployment, and live acceptance tests.

A local or third-party-hosted demo is useful for UI rehearsal but does not
satisfy the official live Databricks, AI Search, or Lakebase gates.

## Integration modes

| Capability | Live mode | Safe fallback |
|---|---|---|
| Language structuring | OpenAI Responses API (`gpt-5.6-sol` by default) | Manual review form |
| Facility evidence | Databricks SQL / governed tables | Seeded demo options labelled as demo |
| Saved plans and feedback | Authenticated owner-scoped Lakebase | Process-local demo store |
| Maps/routes | Restricted Google Routes/Places key | No-key Google Maps link plus seeded comparison |
| Voice | Explicitly enabled server-side ElevenLabs key | Typed multilingual input; voice described as future work |
| Public source discovery | Server-side Tavily key | No external lookup |
| Languages | English, Hindi, Marathi UI strings | English with a visible fallback notice |

Google Routes supports car, walking, bicycle, two-wheeler, and transit modes;
bus and train use transit preferences. Taxi remains a road estimate rather
than a quoted cab fare, and flights require a separate flight-data provider,
so neither is presented as live Google Routes data. The free fallback
must not claim live transit, taxi fares, flight prices, hotel availability, or
real-time capacity. Map/Places facts are supplementary and never replace the
challenge dataset's literal facility evidence.

## Databricks handoff

The Databricks owner should start with:

- [`docs/reference/data-legend-original-brief.pdf`](docs/reference/data-legend-original-brief.pdf)
- [`docs/databricks-team-handoff.md`](docs/databricks-team-handoff.md)
- [`docs/databricks-execution-plan.md`](docs/databricks-execution-plan.md)
- [`docs/data-legend-build-brief.md`](docs/data-legend-build-brief.md)

They must return the catalog/schema/table names, SQL warehouse and Lakebase
resource keys, shortlist input/output shape, documented/conflicting/unknown
sample rows, unsupported fields, and the deployed App URL. Replace the
`TODO_...` table identifiers only after that contract is confirmed.

Databricks deployment uses [`apps/referral-copilot/app.yaml`](apps/referral-copilot/app.yaml).
Its root npm build creates the React assets and `run_app.py` serves them with
the FastAPI routes. Attach the Lakebase resource as `postgres` and the identity
pepper secret as `identity-pepper`. The deployed App must run the exact tested
Git commit and receive secrets/resources through Databricks Apps, never source.

Run the lakehouse pipeline in [`databricks/README.md`](databricks/README.md).
The repository implementation is not submission proof until every required
item in the [official-brief compliance audit](docs/compliance/data-legend-official-brief-audit.md)
and [final submission gate](docs/compliance/final-submission-gate.md) is
verified in the team's Free Edition workspace.

## Build documentation

- Shared agent rules: [`AGENTS.md`](AGENTS.md)
- Final product behavior: [`docs/final-product-plan.md`](docs/final-product-plan.md)
- Fifteen-hour execution: [`docs/overnight-agent-runbook.md`](docs/overnight-agent-runbook.md)
- Testing evidence: [`docs/testing/aven-local-app.tdd.md`](docs/testing/aven-local-app.tdd.md)
- Compliance-change tests: [`docs/testing/data-legend-compliance.tdd.md`](docs/testing/data-legend-compliance.tdd.md)
- Official-brief audit: [`docs/compliance/data-legend-official-brief-audit.md`](docs/compliance/data-legend-official-brief-audit.md)
- Login and persistence security: [`docs/security/login-and-persistence-audit.md`](docs/security/login-and-persistence-audit.md)
- Login/persistence test evidence: [`docs/testing/login-persistence-security.tdd.md`](docs/testing/login-persistence-security.tdd.md)
- Planning/accessibility redesign evidence: [`docs/testing/aven-planning-accessibility-redesign.tdd.md`](docs/testing/aven-planning-accessibility-redesign.tdd.md)

## Known boundaries

- The local result cards are seeded, not challenge-data recommendations.
- Live Databricks deployment, service-principal authorization, and final table
  schemas must be verified in the team's workspace.
- Voice, routing, geocoding, and external evidence require their corresponding
  server-side credentials.
- No custom sign-in is configured. The deployed product uses Databricks
  workspace OAuth; local saved decisions are neither an account nor durable.
- Symptom-first input may support safe care-setting navigation only; it is not
  a diagnosis or specialist-selection engine.
