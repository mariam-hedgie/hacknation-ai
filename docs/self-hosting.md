# Hosting the aven public demo

This puts aven on a public `https://` URL that **you** control, from the public
GitHub repository, with no Databricks account and no help from Mariam.

No Docker required. The built React bundle is committed, so the app is a plain
Python web service that any host can run. A Dockerfile is also provided if you
prefer a container.

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
why it is safe on a public URL. It exists so someone can click through the
workflow without a Databricks login — it is **not** evidence of live retrieval.
[`compliance/final-submission-gate.md`](compliance/final-submission-gate.md)
still requires the Free Edition deployment.

Do not describe this URL as live challenge data.

## Deploy it (Render, ~5 minutes)

Render's free tier runs the app natively from Python. The repo ships a
blueprint, so there is nothing to configure.

1. Push this repository to GitHub (it can stay public — there are no secrets).
2. Open <https://dashboard.render.com/blueprints> → **New Blueprint Instance**.
3. Pick the repository. Render reads [`../render.yaml`](../render.yaml) and
   fills in the runtime, build command, start command, and environment.
4. Click **Apply**. The first build takes 2–3 minutes.

Your site is then live at `https://<service-name>.onrender.com`.

> The free tier sleeps after ~15 minutes idle and takes ~50 seconds to wake.
> **Open the URL a minute before demoing.** Sleeping also clears saved plans,
> because demo persistence is in memory.

### What Render actually runs

Useful if you want to use a different host:

```bash
# from apps/referral-copilot
pip install -r requirements-demo.txt
uvicorn src.backend.api:app --host 0.0.0.0 --port $PORT --proxy-headers
```

with `AVEN_AUTH_MODE=local_demo` and `AVEN_ALLOW_LOCAL_DEMO=true` set.

That is 20 packages, about 25 MB. Anything that can run a Python web process
works: Railway, Fly.io, PythonAnywhere, an EC2/DigitalOcean box behind nginx, or
your own machine.

## Other hosts

### Railway

New Project → Deploy from GitHub repo → set **Root Directory** to
`apps/referral-copilot`, build `pip install -r requirements-demo.txt`, start
with the `uvicorn` line above. Railway injects `$PORT` automatically.

### Docker (Fly.io, Hugging Face Spaces, your own server)

The [`../Dockerfile`](../Dockerfile) builds the React bundle from source and
serves it, producing a 53 MB image.

```bash
docker build -t aven-demo .
docker run --rm -p 8000:8000 aven-demo
```

- **Fly.io:** `fly launch --dockerfile Dockerfile` then `fly deploy`; set
  `internal_port = 8000` in `fly.toml`.
- **Hugging Face Spaces:** create a Space with SDK **Docker** and add
  `sdk: docker` / `app_port: 8000` to the `README.md` front matter.

### Run locally first

```bash
cd apps/referral-copilot
pip install -r requirements-demo.txt
AVEN_AUTH_MODE=local_demo AVEN_ALLOW_LOCAL_DEMO=true \
  uvicorn src.backend.api:app --port 8000
```

Open <http://localhost:8000>.

## Why GitHub Pages will not work

GitHub Pages serves static files only. The planning, safety, and evidence logic
lives in the Python API (`/api/plan` in
[`../apps/referral-copilot/src/backend/api.py`](../apps/referral-copilot/src/backend/api.py)),
so the site needs a running Python process. Every host above provides one free.

## After you change the UI

The React bundle is committed, so rebuild and commit it or the deployed site
will keep serving the old UI:

```bash
npm --prefix apps/referral-copilot run build
git add apps/referral-copilot/frontend/dist && git commit
```

`npm test` at the repo root fails if the bundle is missing or references assets
that are not there.

## Verify the deployment

```bash
curl -s https://<your-url>/api/service-status
```

Expect `"backend_mode": "demo"`. Then in a browser:

1. Open the URL; the React UI loads.
2. Enter a location and pick a care need; confirm the structured request.
3. Confirm three result cards appear, each with a distance and evidence.
4. Save a plan, reopen **My plans**, confirm it is listed.
5. Open the same URL in a private window and confirm **My plans** is empty
   there — that is the isolation check below.

## What the demo deliberately does not do

**Saved plans are per-session and temporary.** They live in process memory,
scoped to a cookie, and are cleared by any restart, redeploy, or free-tier
sleep. Nothing is written to a database. This is the honest behaviour for a
demo with no login — do not present it as the persistence story. Real
cross-session persistence requires Lakebase.

**Visitors are isolated from each other.** Each browser session gets its own
scratch store
([`lakebase.py`](../apps/referral-copilot/src/backend/lakebase.py) —
`_local_session_state`), so one visitor never sees or deletes another's plans.
Pinned by `test_two_demo_visitors_do_not_share_saved_plans` in
[`../apps/referral-copilot/tests/test_api_persistence.py`](../apps/referral-copilot/tests/test_api_persistence.py).

**No live evidence.** Results come from seeded demo facilities. The UI reports
`backend_mode: demo` and must not claim live Databricks evidence.

## Security note: never set `AVEN_AUTH_MODE=databricks` here

Leave it as `local_demo`.

In `databricks` mode the server trusts the `X-Forwarded-User` header, because on
Databricks Apps the Databricks reverse proxy is the authentication boundary and
strips client-supplied copies ([`auth.py`](../apps/referral-copilot/src/auth.py)).
On any other host there is no such proxy, so **any visitor could send that header
themselves and impersonate any owner**, including reading their saved plans.

The same reasoning applies to Databricks credentials generally: do not add a
Databricks token here to try to enable live retrieval. That path needs the
Databricks App, where the service identity authorizes calls and no token is
stored at all.

## Updating

Render and Railway redeploy automatically on push to the tracked branch.
