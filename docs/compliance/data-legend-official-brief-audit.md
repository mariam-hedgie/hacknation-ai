# Data Legend official-brief compliance audit

**Audit date:** 2026-07-19

**Authoritative source:** [`../reference/data-legend-original-brief.pdf`](../reference/data-legend-original-brief.pdf)

**Selected mission:** Referral Copilot

## Verdict

The repository now contains a tested React Referral Copilot vertical slice,
literal evidence and ordinal trust logic, Databricks transformation scripts,
and authenticated owner-scoped Lakebase persistence wiring. It is **not yet
submission-compliant** until the team runs those pieces against the organizer's
10,000-record dataset and demonstrates the exact Git commit as a live
Databricks App in **Free Edition**.

Status meanings:

- **PASS (repo):** verified in local code/tests or documentation.
- **PARTIAL:** a compliant contract or implementation exists, but real challenge
  data or workspace execution is not verified.
- **BLOCKER:** required live evidence is absent and cannot be proved from Git.
- **STRETCH:** optional under the brief, but may improve judging.

## Verification snapshot

Repository checks on 2026-07-19:

- 237 Python tests passed, including owner isolation, data minimization,
  managed Lakebase OAuth, API save/reload/feedback/delete, literal raw-source
  receipt validation, distance/type mapping, safety, and accessibility.
- 8 Node contract tests passed; the React production build and lint completed.
- Both npm lockfiles reported 0 known vulnerabilities; `pip check` reported no
  broken installed requirements; `git diff --check` reported no patch errors.
- The current shell has no configured SQL, Vector Search, Genie, Lakebase, or
  MLflow resource and no Databricks CLI. Backend mode is therefore `demo`.
  These local results do not prove any live platform gate below.

## Core requirements

| Official requirement | Page | Status | Repository evidence | Remaining proof/action |
|---|---:|---|---|---|
| Choose one mission and complete its minimum workflow | 2 | PASS (repo) | Referral Copilot is fixed in [`../final-product-plan.md`](../final-product-plan.md) and [`../../README.md`](../../README.md). | Keep the demo centered on this one workflow. |
| Use the Databricks Data Intelligence Platform to structure the supplied 10k messy facility records | 2 | PARTIAL | [`../../databricks/01_ingest_and_profile.sql`](../../databricks/01_ingest_and_profile.sql) and [`../../databricks/02_build_evidence_tables.py`](../../databricks/02_build_evidence_tables.py). | Subscribe to the linked dataset in Free Edition, run both files, confirm 10,000 rows, record actual schema/coverage, and preserve raw values. |
| Every important output traces to supporting facility text | 2 | PARTIAL | Both retrieval paths perform literal-span validation. The active Vector Search mapper checks extracted spans against preserved raw source fields and emits field + row ID receipts; invalid spans fail closed. | Rebuild the corrected searchable table/index, query real challenge rows in the deployed app, and click through at least three receipts. Seeded demo receipts do not satisfy this requirement. |
| Trust logic reasons about confidence and corroboration rather than keyword retrieval alone | 2 | PARTIAL | `src/trust.py` uses distinct verified source fields and ordinal `weak/supported/strong/conflicting` states; [`../../databricks/03_build_trust_assessment.sql`](../../databricks/03_build_trust_assessment.sql) precomputes inspectable inputs. | Validate claim rules against actual facility records; add reviewer-confirmed conflicts. Never present the ordinal label as a clinical-quality score or probability. |
| Flag suspicious/incomplete data and communicate uncertainty | 2 | PARTIAL | Missing fields, broken-span rejection, conflict precedence, and explicit `not documented` copy are tested. | Inspect weak/incomplete review query output on real data and confirm the UI exposes it. |
| Clear, nontechnical Databricks App journey | 2 | PARTIAL | The React flow uses request, confirmation, action plan, proof, unknowns, save, feedback, and My plans; FastAPI serves the production build. | Deploy and test this journey in a Databricks App. Primary demo persona should be a patient coordinator/community or NGO planner, not “any user.” |
| Persist notes, overrides, shortlists, scenarios, or review decisions beyond one session | 2 | PARTIAL | `/api/plans` resolves Databricks proxy identity server-side, derives a pseudonymous owner, obtains rotating Lakebase OAuth credentials, and binds `owner_id` on save/read/list/delete/feedback. Payload minimization and isolation are tested. | Attach the `postgres` Lakebase resource and `identity-pepper` secret, then prove save -> browser refresh/new session -> reopen in Free Edition. Local demo state is explicitly process-local and does not satisfy this gate. |
| Demo live on Databricks Free Edition | 2, 4, 5 | **BLOCKER** | No live URL or workspace evidence is stored in the repo. | Deploy early in Free Edition only; do not submit an enterprise or paid organizational workspace. Record URL and commit SHA. |

## Referral Copilot minimum workflow

| Official step | Page | Status | Evidence / remaining action |
|---|---:|---|---|
| User enters a location and care need | 3 | PASS (repo) | Intake validation and local UI/tests cover both. |
| User receives an evidence-attached shortlist | 3 | PARTIAL | Ranking and receipt contracts pass locally; must replace seeded cards with challenge-table results in the deployed app. |
| Every candidate shows distance | 3 | PARTIAL | The active pipeline carries facility coordinates and computes a clearly labelled straight-line distance from known golden-path city centres; unknown origins remain unknown and Maps supplies the route action. | Rebuild against real coordinates, validate city/coordinate conflicts, and show the three golden-path distances in the deployed app. Never present straight-line distance as route distance. |
| Every candidate shows matching evidence | 3 | PARTIAL | Row/column/literal-span receipt is implemented; verify on live rows. |
| Every candidate shows gaps | 3 | PASS (repo) | `missing_fields` becomes visible cautions; `not documented` is not treated as unavailable. Verify UI-owner implementation preserves this wording. |
| User saves to a shortlist | 3 | PARTIAL | React save succeeds only after the persistence API confirms it; the My plans screen reloads owner-scoped records. Live Lakebase cross-session proof is still required. |

## Claims, evidence, and data-desert safeguards

| Rule/research question | Page | Status | Audit finding |
|---|---:|---|---|
| Capability, procedure, and equipment values are claims, not facts | 4 | PASS (repo) | Code calls them claims/evidence and requires a literal receipt before `documented`. |
| Strong evidence must be distinguishable from weak evidence | 4–5 | PASS (repo) | Ordinal trust levels are based on count of distinct verified fields and preserve the underlying receipts. |
| Sparse data must not be presented as a medical desert | 4–5 | PASS (repo), UI verification pending | Logic says `not documented`; final map/results must visibly distinguish “no matching records in this dataset” from “no facility exists.” |
| App double-checks its own work | 5 | PARTIAL | Deterministic literal-span validator and evaluation cases exist. Actual-data test results and optional MLflow traces are not yet recorded. |

## Platform, submission, and judging

| Official requirement/signal | Page | Status | Required final evidence |
|---|---:|---|---|
| Databricks Apps live surface | 4–5 | **BLOCKER** | Public/judge-accessible App URL loading the exact submitted commit. |
| Serverless compute in Free Edition | 4–5 | **BLOCKER** | Workspace/app settings screenshot or live verification. |
| Mosaic AI Vector Search used well | 4–5 | **BLOCKER** | Create an index over `facility_source_chunks`, attach it as an App resource, and show one retrieval whose literal span is revalidated before display. Do not use semantic similarity itself as evidence. |
| Lakebase used for retained human actions | 4–5 | PARTIAL | Managed-resource coordinates, short-lived OAuth credentials, schema safety checks, minimized owner-scoped plan/feedback endpoints, and React reload/delete flows are wired and tested. Attach the resource and pass the live cross-session/two-user test. |
| Agent Bricks and Genie | 4 | Not independently mandatory in the wording, but listed in the primary stack | Only add if they improve the golden path and are available in Free Edition. Do not claim them without a visible, testable use. |
| MLflow 3 | 3–4 | PARTIAL / stack signal | MLflow 3 is a deployment dependency and the retrieval -> validation -> ranking stages use bounded trace spans. Configure an experiment and show a real trace; no chain-of-thought is required or appropriate. |
| Submit Git repository | 5 | PASS (repo) | Confirm final pushed commit and clean worktree. |
| One-minute demo explains user, workflow, technical approach, tradeoffs | 5 | **BLOCKER** | Rehearse and time the final script; include one meaningful uncertainty/tradeoff. |

The PDF's “Primary Tech Stack” is an intended platform architecture and the
technical rubric specifically names Apps, serverless compute, Vector Search,
and Lakebase. Treat those four as final submission gates. Agent Bricks, Genie,
and MLflow should never be checked off merely because they appear in a slide.

## Exact final blockers

1. In a Databricks **Free Edition** workspace, access the organizer-linked
   Marketplace listing from page 4.
2. Run the phase 1 profile and confirm the source has 10,000 records; document
   actual field names, types, null coverage, duplicates, and unsupported facts.
3. Run phases 2–3 and prove `broken_receipts = 0` with real challenge data.
4. Review weak/incomplete rows and enter at least one validated conflict only if
   a real conflict exists; do not seed a fake conflict into production data.
5. Create an AI/Vector Search index over literal source chunks and revalidate
   returned spans before display.
6. Attach a Lakebase Autoscaling resource as `postgres`, attach the
   `identity-pepper` secret, and pass save/reload plus two-user isolation from a
   new session. The code boundary is complete; workspace proof is not.
7. Connect the app to live facility results without
   changing its evidence/unknown wording or silently falling back to seeded
   results.
8. Deploy the exact final Git SHA as a Databricks App and test in a fresh browser.
9. Record the App URL, commit SHA, test time, and one-minute demo owner in
   [`final-submission-gate.md`](final-submission-gate.md).

## Stretch priorities after all blockers pass

1. MLflow trace for extraction -> scoring -> ranking receipts.
2. Validator queue/self-correction using real internal inconsistencies.
3. India map that visually separates weak/no dataset coverage from a supported
   medical-desert conclusion.
4. Multilingual voice as an access layer, while keeping confirmation before
   search and never sending raw health information to unrelated web services.

## Current official platform references

- [Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition)
- [Databricks App resources and least-privilege service identity](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources)
- [Lakebase App resource](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)

These links explain current mechanics; the challenge PDF controls hackathon
eligibility and judging.
