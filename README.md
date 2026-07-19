# aven

aven helps people turn a care-access question into a short, understandable list of facility options. It keeps the supporting evidence, unknowns, and next action visible so a person can decide what to do next.

## What it does

- Collects a typed care request and lets the person review it before searching.
- Shows facility options with supporting excerpts, cautions, and a clear next step.
- Keeps emergency guidance separate from normal planning.
- Supports English, Hindi, and Marathi interface copy.

## Run locally

From the repository root, do this once:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r apps/referral-copilot/requirements.txt
cd apps/referral-copilot
npm install
npm run build
```

Then start the app with the project virtual environment. This avoids relying on a system `python` command that may point to the wrong version:

```bash
cd apps/referral-copilot
AVEN_AUTH_MODE=local_demo AVEN_ALLOW_LOCAL_DEMO=true DATABRICKS_APP_PORT=8010 ../../.venv/bin/python run_app.py
```

Open [http://127.0.0.1:8010](http://127.0.0.1:8010). If the terminal says port `8010` is already in use, the app is already running—open that link instead of starting a second copy.

### Optional local request drafting

The app works without a model. To turn a free-text note into an editable draft
without using OpenAI, install Ollama, then run:

```bash
ollama serve
ollama pull gemma3:4b
```

Keep the default `AVEN_NLP_PROVIDER=ollama`, `OLLAMA_HOST`, and `OLLAMA_MODEL`
values from `.env.example`. Ollama runs server-side; the result is always an
editable suggestion and never starts a search by itself.

## How to use aven

1. Describe the care need or choose a task.
2. Enter the city, urgency, travel preference, and any budget or distance limit.
3. Review the structured request and correct anything that is wrong.
4. Compare the returned options, including the evidence and unknowns.
5. Open the map link or contact source to confirm time-sensitive details before travelling.

For an emergency, use local emergency services rather than waiting for a normal recommendation.

## Important local-demo boundary

The local app can use a static facility snapshot for rehearsal. It is not a live availability, routing, booking, or persistence service. Confirm current details with the relevant provider before acting.

For deployment, configure the project’s managed data and persistence resources in the target environment. Do not add credentials to source control.
