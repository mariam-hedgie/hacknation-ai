# Self-hosting the aven public demo

This deploys a **public demo** of aven that you can host yourself, from the
public GitHub repository, without a Databricks account and without Mariam.

## What this is and is not

| | Public demo (this document) | Databricks App ([`databricks-team-handoff.md`](databricks-team-handoff.md)) |
|---|---|---|
| Who deploys it | You | The Databricks account owner |
| Data | Seeded demo facilities | Live challenge dataset |
| Retrieval | Deterministic seeded logic | AI Search over 10k rows |
| Saved plans | In-memory, per browser session | Lakebase, survives restarts |
| Login | None (anonymous) | Databricks OAuth |
| Secrets needed | None | Identity pepper, Lakebase, AI Search |
| Satisfies the submission gate | **No** | Yes |

The demo contacts no Databricks service and holds no secrets, which is exactly
why it is safe to put on a public URL. It is a way to let someone click through
the workflow without a Databricks login — **not** evidence of live Databricks
retrieval. [`compliance/final-submission-gate.md`](compliance/final-submission-gate.md)
still requires the Free Edition deployment.

Do not describe this URL as live challenge data.

## Why not GitHub Pages

GitHub Pages serves static files only. The planning, safety, and evidence logic
lives in the Python API (`/api/plan` in
[`../apps/referral-copilot/src/backend/api.py`](../apps/referral-copilot/src/backend/api.py)),
so the site needs a running Python process. Any host below provides one on a
free tier.

## Deploy

The repository ships a [`../Dockerfile`](../Dockerfile) that builds the React
bundle and serves it from the FastAPI app in a single container. Any container
host works; pick one.

### Render (has a one-click blueprint)

1. Push to a public GitHub repository.
2. Go to <https://dashboard.render.com/blueprints> → **New Blueprint Instance**.
3. Select the repository. Render reads [`../render.yaml`](../render.yaml) and
   configures the service automatically.
4. **Apply**. First build takes roughly 3–5 minutes.

Your URL will be `https://<service-name>.onrender.com`.

> Render's free tier sleeps after ~15 minutes idle, and the next request takes
> ~50 seconds to wake. **Open the URL a minute before a demo.** Sleeping also
> clears saved plans, because demo persistence is in-memory.

### Fly.io

```bash
fly launch --dockerfile Dockerfile --no-deploy
fly deploy
```

Set `internal_port = 8000` in the generated `fly.toml`.

### Railway

New Project → Deploy from GitHub repo. Railway detects the `Dockerfile` and
injects `$PORT`, which the container already respects. No configuration needed.

### Hugging Face Spaces

Create a Space with SDK **Docker**, push the repository, and add to the top of
`README.md`:

```yaml
---
sdk: docker
app_port: 8000
---
```

### Run it locally first

```bash
docker build -t aven-demo .
docker run --rm -p 8000:8000 aven-demo
```

Open <http://localhost:8000>.

## Verify the deployment

```bash
curl -s https://<your-url>/api/service-status
```

Expect `"backend_mode": "demo"`. Then in a browser:

1. Open the URL; the React UI loads.
2. Enter a location and pick a care need; confirm the structured request.
3. Confirm three result cards appear, each with a distance and evidence.
4. Save a plan, reopen **My plans**, and confirm it is listed.
5. Open the same URL in a private window and confirm **My plans** is empty
   there. This is the isolation check described below.

## What the demo deliberately does not do

**Saved plans are per-session and temporary.** They live in process memory,
scoped to a cookie, and are cleared by any restart or redeploy. Nothing is
written to a database. This is the honest behaviour for a demo with no login —
do not present it as the persistence story. The real cross-session persistence
proof requires Lakebase.

**Visitors are isolated from each other.** Each browser session gets its own
scratch store
([`lakebase.py`](../apps/referral-copilot/src/backend/lakebase.py) —
`_local_session_state`), so one visitor never sees or deletes another's plans.
Pinned by `test_two_demo_visitors_do_not_share_saved_plans` in
[`../apps/referral-copilot/tests/test_api_persistence.py`](../apps/referral-copilot/tests/test_api_persistence.py).

**No live evidence.** Results come from seeded demo facilities. The UI reports
`backend_mode: demo` and must not claim live Databricks evidence.

## Security note: never set `AVEN_AUTH_MODE=databricks` here

The image hardcodes `AVEN_AUTH_MODE=local_demo`. Leave it that way.

In `databricks` mode the server trusts the `X-Forwarded-User` header, because on
Databricks Apps the Databricks reverse proxy is the authentication boundary and
strips client-supplied copies ([`auth.py`](../apps/referral-copilot/src/auth.py)).
On any other host there is no such proxy, so **any visitor could send that header
themselves and impersonate any owner**, including reading their saved plans.

The same reasoning applies to Databricks credentials generally: do not add a
Databricks token to this deployment to try to enable live retrieval. That path
needs the Databricks App, where the service identity authorizes calls and no
token is stored at all.

## Updating

Render, Railway, and Fly redeploy on push to the tracked branch. Rebuild
locally with `docker build` after changing frontend or backend code.
