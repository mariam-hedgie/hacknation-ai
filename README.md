# aven

aven helps people turn a care-access question into a short, understandable list of facility options. It keeps the supporting evidence, unknowns, and next action visible so a person can decide what to do next.

## What it does

- Collects a typed care request and lets the person review it before searching.
- Shows facility options with supporting excerpts, cautions, and a clear next step.
- Keeps emergency guidance separate from normal planning.
- Supports English, Hindi, and Marathi interface copy.

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r apps/referral-copilot/requirements.txt
cd apps/referral-copilot
npm install
npm run build
AVEN_AUTH_MODE=local_demo AVEN_ALLOW_LOCAL_DEMO=true python run_app.py
```

Open [http://localhost:8010](http://localhost:8010).

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
