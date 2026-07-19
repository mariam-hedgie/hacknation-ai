# Aven end-to-end and external audit — 2026-07-19

## Verdict

The integrated local demo golden path passes. The live Databricks submission
path is **not yet an end-to-end pass**: the running UI truthfully reports seeded
demo data, and the production authentication/Lakebase modules are not wired
into `app.py`.

## Browser demo exercised

Integrated branch: `main`

1. Opened the landing page at `http://127.0.0.1:8512`.
2. Chose `Referral or procedure`.
3. Entered `Dialysis referral`, origin `Patna, Bihar`, bus/train travel, and a
   public-facility preference.
4. Reviewed the extracted summary and confirmed it.
5. Received exactly three explicitly seeded demo routes with documented,
   unknown, and conflict states.
6. Saved the first plan and submitted bounded feedback.
7. Verified the saved plan appeared under `My plans`.
8. Browser console audit returned zero warnings/errors.

This proves the integrated local UI flow and session state. It does not prove
Databricks SQL, AI Search/Vector Search, Agent Bricks, Lakebase, OAuth identity,
or cross-session persistence.

## Automated and external checks

| Check | Result | Evidence |
|---|---|---|
| Python suite | PASS | `python -m unittest discover -s apps/referral-copilot/tests -q`: 154 tests |
| Python compilation | PASS | `python -m compileall -q apps/referral-copilot databricks` |
| Installed Python consistency | PASS | `python -m pip check`: no broken requirements |
| Python vulnerability database | PASS at scan time | `uvx --python .venv/bin/python pip-audit --local`: no known vulnerabilities |
| Node tests | PASS | `npm test`: 4 tests |
| npm vulnerability database | PASS at scan time | `npm audit --omit=dev --audit-level=high`: 0 vulnerabilities |
| Known secret-pattern history scan | PASS for scoped patterns | No GitHub/OpenAI/Tavily/Google-key pattern filenames found in Git history |
| Bandit Python scan | REVIEW | 0 high, 7 medium, 1 low; triage below |
| GitHub Dependabot alerts | NOT AVAILABLE | Disabled for the private repository |
| GitHub secret scanning | NOT AVAILABLE | Disabled for the private repository/current token cannot audit it |
| GitHub code scanning | NOT AVAILABLE | No code-scanning setup |
| GitHub Actions | NOT AVAILABLE at audit start | No workflow runs existed |

Vulnerability results are time-bound snapshots, not guarantees.

## TDD deployment fix

User journey: as a Databricks Apps user, I need Streamlit to bind to the port
selected by the platform so the deployed app can receive requests.

- RED: `test_deployment_config.py` failed because `app.yaml` hard-coded port
  `8000` and address `0.0.0.0`.
- GREEN: `app.yaml` now uses `['streamlit', 'run', 'app.py']`; Databricks injects
  `STREAMLIT_SERVER_PORT` and `STREAMLIT_SERVER_ADDRESS`.
- Regression test and the full 154-test suite pass.

## Security scanner triage

- Six Bandit SQL findings are low-confidence scanner matches around dynamic
  table identifiers. User data remains parameter-bound, and table identifiers
  are restricted by `_IDENTIFIER` before interpolation. Keep the validation
  tests and do not accept table names from requests.
- The `urlopen` finding calls one fixed HTTPS Tavily endpoint, and returned URLs
  are separately scheme/host validated before display. Keep redirects and
  outbound-host policy under review for production.
- The low-severity swallowed exception is in optional MLflow attribute tracing;
  it can hide telemetry failure but does not change care results.

## Blocking findings before calling the submission live

### P0 — authentication boundary is implemented but bypassed by the UI

`src/auth.py` correctly fails closed around Databricks proxy identity, but
`app.py` does not call it. Instead, the Account popover accepts a name/email for
a local demo profile. A typed email is not authentication.

Required fix: in Databricks mode, obtain the platform forwarded identity from
the Streamlit request context, call `resolve_identity`, and remove/disable the
local email-profile control. Configure `AVEN_IDENTITY_PEPPER` from a Databricks
secret. Verify two-user isolation in the deployed workspace.

### P0 — persistence seam is implemented but bypassed by the UI

`src/persistence.py` provides owner-scoped, minimized Lakebase persistence, but
the visible Save/Feedback flow writes session state and `src/profiles.py` may
write raw email, request location/capability history, ratings, and blocklists to
local JSON. `src/backend/lakebase.py` is still a TODO fallback.

Required fix: construct `PersistentSqlPlanStore` from the managed Lakebase app
resource and authenticated pseudonymous owner; route save/load/feedback/delete
through it; prohibit local JSON persistence in Databricks mode; verify a saved
decision survives a new browser session without leaking to another user.

### P0 — live challenge data path is not demonstrated

The UI itself states that Vector Search, Agent Bricks, and Lakebase are not
connected. Before judging, deploy the 10k-record evidence pipeline, query real
literal source spans, and show a live Databricks App URL plus a persisted user
decision.

### P1 — deprecated Streamlit component

The suite emits a warning that `st.components.v1.html` is removed after
2026-06-01. The installed runtime still rendered it locally, but replace the
scroll-reveal iframe with `st.iframe` or ordinary Streamlit/CSS before relying
on a newer deployment runtime.

### P1 — hosted audit coverage is disabled

Enable Dependabot, secret scanning where the repository plan supports it, and
CodeQL or another code-scanning workflow. Local scanners cannot replace the
repository-hosted controls.

## Live acceptance gate

Do not label the full system PASS until all of these are captured:

- live Databricks App URL and deployment logs;
- app service principal permissions for the SQL warehouse, evidence tables,
  AI Search index, Lakebase, and secrets;
- one real 10k-record query with literal source citations;
- two authenticated users proving plan isolation;
- one saved plan reopened in a new session;
- one deletion/expiry test;
- no raw identity, health narrative, credentials, or audio in logs/storage;
- final Hindi and Marathi keyboard/mobile smoke tests; and
- final responsive map/text-fallback accessibility test.

