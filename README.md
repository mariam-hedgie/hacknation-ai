# Aven

**The right care route, with proof.**

Aven is the Hack-Nation Data Legend Referral Copilot. A person describes a
care-access need in natural language, reviews the structured request, and gets
an actionable facility plan whose evidence and unknowns remain visible. Aven
does not diagnose, prescribe, determine benefit eligibility, or promise price,
stock, availability, outcomes, or crowd levels.

The current repository contains a deterministic local vertical slice plus
interfaces for Databricks, maps, persistence, multilingual text, and
ElevenLabs. The seeded path stays usable when live services are unavailable.

## Golden-path demo

1. Enter a typed request in English, Hindi, or Marathi.
2. Choose the task: referral/procedure, refill, lab, symptom-first, or follow-up.
3. Set urgency, cost sensitivity, travel tolerance, and public/private preference.
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

### Start the frontend

```bash
source .venv/bin/activate            # Windows: .venv\Scripts\activate
cd apps/referral-copilot
streamlit run app.py
```

Streamlit prints a local URL, normally **<http://localhost:8501>** — open it in
your browser to view the app. The terminal running `streamlit run` stays
attached to the server; press `Ctrl+C` there to stop it. If it prompts for an
onboarding email on first run, press Enter to skip it, or start it with
`streamlit run app.py --server.headless true` to suppress the prompt.

Use `streamlit run app.py --server.port 8502` to run on a different port if
8501 is already in use.

### Run validation

```bash
cd /path/to/hacknation-ai
python3 -m unittest discover -s apps/referral-copilot/tests -v
python3 -m compileall -q apps/referral-copilot
npm run check:elevenlabs
```

The ElevenLabs check reports configuration only; it does not print the key.

## Integration modes

| Capability | Live mode | Safe fallback |
|---|---|---|
| Facility evidence | Databricks SQL / governed tables | Seeded demo options labelled as demo |
| Saved plans and feedback | Lakebase or approved Databricks write path | Current Streamlit session |
| Maps/routes | Restricted Google Maps key | ORS road modes, then offline comparison labels |
| Voice | Server-side ElevenLabs key | Typed input |
| Languages | English, Hindi, Marathi UI strings | English with a visible fallback notice |

Google supports the broadest planned routing experience. The free fallback
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
The deployed App must run the exact tested Git commit and receive secrets and
resources through Databricks Apps rather than source code.

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

## Known boundaries

- The local result cards are seeded, not challenge-data recommendations.
- Live Databricks deployment, service-principal authorization, and final table
  schemas must be verified in the team's workspace.
- Voice, routing, geocoding, and external evidence require their corresponding
  server-side credentials.
- Symptom-first input may support safe care-setting navigation only; it is not
  a diagnosis or specialist-selection engine.
