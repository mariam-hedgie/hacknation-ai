# Data Legend official-brief compliance audit

**Audit date:** 2026-07-19

**Authoritative source:** [`../reference/data-legend-original-brief.pdf`](../reference/data-legend-original-brief.pdf)

**Selected mission:** Referral Copilot

## Verdict

The repository now contains a tested local Referral Copilot vertical slice,
literal evidence and ordinal trust logic, Databricks transformation scripts,
and a Lakebase-compatible persistence boundary. It is **not yet
submission-compliant** until the team runs those pieces against the organizer's
10,000-record dataset and demonstrates the exact Git commit as a live
Databricks App in **Free Edition**.

Status meanings:

- **PASS (repo):** verified in local code/tests or documentation.
- **PARTIAL:** a compliant contract or implementation exists, but real challenge
  data or workspace execution is not verified.
- **BLOCKER:** required live evidence is absent and cannot be proved from Git.
- **STRETCH:** optional under the brief, but may improve judging.

## Core requirements

| Official requirement | Page | Status | Repository evidence | Remaining proof/action |
|---|---:|---|---|---|
| Choose one mission and complete its minimum workflow | 2 | PASS (repo) | Referral Copilot is fixed in [`../final-product-plan.md`](../final-product-plan.md) and [`../../README.md`](../../README.md). | Keep the demo centered on this one workflow. |
| Use the Databricks Data Intelligence Platform to structure the supplied 10k messy facility records | 2 | PARTIAL | [`../../databricks/01_ingest_and_profile.sql`](../../databricks/01_ingest_and_profile.sql) and [`../../databricks/02_build_evidence_tables.py`](../../databricks/02_build_evidence_tables.py). | Subscribe to the linked dataset in Free Edition, run both files, confirm 10,000 rows, record actual schema/coverage, and preserve raw values. |
| Every important output traces to supporting facility text | 2 | PARTIAL | Literal-span validation and row/column receipts in `src/domain.py`, `src/databricks_adapter.py`, `src/trust.py`, and their tests. | Query the real evidence table in the deployed app and click through at least three real receipts. Seeded demo receipts do not satisfy this requirement. |
| Trust logic reasons about confidence and corroboration rather than keyword retrieval alone | 2 | PARTIAL | `src/trust.py` uses distinct verified source fields and ordinal `weak/supported/strong/conflicting` states; [`../../databricks/03_build_trust_assessment.sql`](../../databricks/03_build_trust_assessment.sql) precomputes inspectable inputs. | Validate claim rules against actual facility records; add reviewer-confirmed conflicts. Never present the ordinal label as a clinical-quality score or probability. |
| Flag suspicious/incomplete data and communicate uncertainty | 2 | PARTIAL | Missing fields, broken-span rejection, conflict precedence, and explicit `not documented` copy are tested. | Inspect weak/incomplete review query output on real data and confirm the UI exposes it. |
| Clear, nontechnical Databricks App journey | 2 | PARTIAL | Local Streamlit flow uses request, confirmation, action plan, proof, unknowns, save, and feedback. | Deploy and test this journey in a Databricks App. Primary demo persona should be a patient coordinator/community or NGO planner, not “any user.” |
| Persist notes, overrides, shortlists, scenarios, or review decisions beyond one session | 2 | PARTIAL | `src/persistence.py`, [`../../databricks/lakebase_schema.sql`](../../databricks/lakebase_schema.sql), and persistence contract tests. | Attach a Lakebase Autoscaling resource, wire the executor into the UI backend, then prove save -> browser refresh/new session -> reopen. Session state alone fails the brief. |
| Demo live on Databricks Free Edition | 2, 4, 5 | **BLOCKER** | No live URL or workspace evidence is stored in the repo. | Deploy early in Free Edition only; do not submit an enterprise or paid organizational workspace. Record URL and commit SHA. |

## Referral Copilot minimum workflow

| Official step | Page | Status | Evidence / remaining action |
|---|---:|---|---|
| User enters a location and care need | 3 | PASS (repo) | Intake validation and local UI/tests cover both. |
| User receives an evidence-attached shortlist | 3 | PARTIAL | Ranking and receipt contracts pass locally; must replace seeded cards with challenge-table results in the deployed app. |
| Every candidate shows distance | 3 | PARTIAL | Domain and adapter support distance, but real coordinates/geocoding and actual facility distances are not workspace-verified. Never show route distance as straight-line distance without labeling it. |
| Every candidate shows matching evidence | 3 | PARTIAL | Row/column/literal-span receipt is implemented; verify on live rows. |
| Every candidate shows gaps | 3 | PASS (repo) | `missing_fields` becomes visible cautions; `not documented` is not treated as unavailable. Verify UI-owner implementation preserves this wording. |
| User saves to a shortlist | 3 | PARTIAL | Local/session save works; Lakebase cross-session proof is still required. |

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
| Lakebase used for retained human actions | 4–5 | PARTIAL | Schema and adapter exist; attach resource and pass cross-session test. |
| Agent Bricks and Genie | 4 | Not independently mandatory in the wording, but listed in the primary stack | Only add if they improve the golden path and are available in Free Edition. Do not claim them without a visible, testable use. |
| MLflow 3 | 3–4 | STRETCH / stack signal | Trace extraction -> scoring -> ranking if time permits; no chain-of-thought is required or appropriate. Log inputs, tool/result metadata, receipts, ordinal trust inputs, output, latency, and final user action. |
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
6. Attach a Lakebase Autoscaling resource, run the schema, wire
   `PersistentSqlPlanStore`, and pass save/reload from a new session.
7. Connect the UI-owner app to live facility and persistence boundaries without
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
