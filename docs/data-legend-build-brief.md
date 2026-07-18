# Data Legend: rule-grounded build brief

## Source of truth

The original sponsor brief is preserved at
[`reference/data-legend-original-brief.pdf`](reference/data-legend-original-brief.pdf).
This document is a working interpretation for the team. If a requirement,
wording, deadline, eligible technology, or judging expectation is disputed,
unclear, or changes, **read the original PDF first and follow it over this
summary**. Do not use this document to invent a requirement that the PDF does
not establish.

## The challenge in plain English

The challenge provides roughly 10,000 messy Indian healthcare-facility
records (51 columns). Facility claims can be incomplete, ambiguous,
contradictory, or stale. The central problem is not merely finding records: it
is helping a user make a trustworthy, auditable decision despite noisy data.

The team must build and deploy a live application using **Databricks Apps on
Databricks Free Edition**. The brief presents four possible missions:

1. Facility Trust Desk
2. Medical Desert Planner
3. Referral Copilot
4. Data Readiness Desk

Choose one as the primary mission. A product can borrow a small supporting
idea from another mission, but it must not become four disconnected products.

## Recommended mission and product direction

**Primary mission: Referral Copilot.**

Working concept: **Aven**, a multilingual, cost- and
access-aware referral planner. It helps a patient or primary-care clinician
turn a confirmed care need and access constraints into a small number of
evidence-backed route options. It is not a diagnostic chatbot and does not
claim to know real-time availability or fees without a source.

Core workflow:

```text
Confirmed need + location + constraints
  -> retrieve facility evidence from the challenge data
  -> compare feasible options transparently
  -> user or clinician reviews, changes, and saves a route
  -> collect optional access outcome feedback
```

The differentiator is a **no-surprises referral casefile**: every option
shows what supports it, what contradicts it, and what is unknown.

## Bare-minimum deliverable requirements

The minimum credible submission should provide all of the following.

1. **A live deployed Databricks App.** A notebook, slide deck, or local-only
   prototype is not enough.
2. **One selected mission.** State it plainly in the README and demo.
3. **Use of the supplied facility data.** The application should operate on
   the challenge data, not only hard-coded outputs.
4. **Traceability to source text.** Each material facility claim or
   recommendation must let a user inspect its originating record/text.
5. **Visible uncertainty.** Display evidence strength, missing information,
   and contradictions rather than treating every facility claim as fact.
6. **Persisted user state.** Save useful interaction data such as a
   shortlist, note, override, saved scenario, or planner feedback, then show
   that it can be reopened.
7. **A trustworthy action or outcome.** Give the user an understandable next
   step, not an unexplained score or generic chat response.

## Evidence and unverifiable-data policy

The raw dataset contains claims, not ground truth. Use explicit statuses:

| Evidence state | Meaning | Product behavior |
|---|---|---|
| Supported by record | The source text supports the displayed claim | Show excerpt and record link/identifier. |
| Conflicting records | Available records disagree | Show the conflict; lower confidence; do not pick a winner silently. |
| Not documented | The provided data does not establish the claim | Say unknown and provide a verification action if useful. |
| External corroboration | An official public source separately supports a claim | Show URL and retrieval time; keep it distinct from dataset evidence. |
| User-reported | A user supplied a preference or fact | Do not turn it into a facility fact. |

Never fabricate or imply certainty about:

- treatment prices or insurance/scheme eligibility;
- real-time doctor availability, wait times, or busy hours;
- clinical outcomes, clinician quality, or medical appropriateness;
- service capability when source text is absent or contradictory.

When a fact cannot be verified, say so plainly: for example, `Consultation
price: not documented - call before travel.` An explicit unknown is a feature,
not a failure.

## Aven: ambitious feature order

Build in this order. Do not start a lower-priority item until the earlier one
works in the deployed app.

### 1. Golden path - required

- User selects a confirmed specialty/capability, location, urgency, travel
  tolerance, and spending preference.
- App returns three intentionally different facility options: strongest
  verified fit, lowest known-cost/public route, and closest plausible route.
- Each option contains source excerpts, an uncertainty label, and a clear
  next step.
- User saves a shortlist or overrides the recommendation with a note.
- The saved plan is persisted and can be reopened.

### 2. Evidence casefile - required for a strong score

- Facility card expands into supporting text, conflicting text, and missing
  information.
- Ranking explanation names the user constraints that affected the order.
- A small in-product activity panel records input, evidence used, result,
  uncertainty, and user action.

### 3. Access-aware route comparison - high-value extension

- Sliders: urgency, travel tolerance, budget sensitivity, and evidence
  preference.
- Seeded estimates for travel and overnight needs, clearly labeled as demo
  estimates unless backed by an official source.
- Rural and urban scenarios demonstrate different tradeoffs.
- Show a route as a composed plan, rather than only a hospital marker.

### 4. Multilingual voice intake - polish extension

- ElevenLabs captures a patient request in a tested language.
- Show a structured summary and require confirmation before any search or
  ranking.
- Read an approved referral handoff/checklist back in the selected language.
- Keep the API key server-side. Voice is an accessibility layer, not hidden
  decision-making.

### 5. Symptom-to-care-setting triage - only with safeguards

- A symptom can initiate a short, safety-focused intake, but it must never
  diagnose.
- Obvious emergency signals must route to urgent/emergency guidance before
  ordinary facility comparison.
- Suggest a possible next care setting only as a reviewable prompt for the
  user/clinician; do not say the user has a condition.

### 6. Feedback loop - stretch, but memorable

- After a visit attempt, record access feedback such as service unavailable,
  price differed, accepted, or not visited.
- Treat it as an access report, not a clinical-quality review.
- Surface disputed facility claims for future review rather than silently
  changing the truth of a facility record.

## A practical Databricks implementation

The brief suggests technologies including Databricks Apps, Agent Bricks,
Genie, MLflow 3, Mosaic AI Vector Search, and Lakebase. These are options,
not a requirement to adopt every product. The required sponsor centerpiece is
the deployed Databricks App. Use the smallest stack that produces a reliable
vertical slice.

Recommended minimal architecture:

```text
Raw facility table
  -> cleaned facility/evidence table
  -> transparent ranking function
  -> Databricks App (map, comparison, evidence casefile)
  -> saved plans / notes / feedback table
```

Suggested tables:

```text
facilities_raw
facility_claims_evidence
saved_referral_plans
saved_shortlists
user_overrides_notes
access_feedback
```

Keep ranking interpretable. For a seeded demo, calculate a visible weighted
score from facility-fit evidence, travel burden, budget preference, and
uncertainty penalty. Let the user change the weights and show why ranking
changes. Do not present an opaque model score as medical truth.

Persistence can be as simple as writing the selected option, constraints,
timestamp, and note to a durable Databricks-backed table. Demonstrate it by
saving a plan, navigating away, and reopening it.

## Evaluation plan

Prepare 5-10 fixed, seeded scenarios before the demo. Include at least:

- a facility with strong evidence;
- a facility with conflicting evidence;
- a facility with key data absent;
- a rural long-distance access scenario;
- an urban low-cost versus convenience tradeoff;
- a user override that is saved and reopened.

For each case, verify: evidence trace accuracy, correct unknown/conflict
labels, sensible ranking response to sliders, persisted data, and safe
language. A reliable deterministic demo is more valuable than a fragile live
integration.

## Demo structure

1. State the user problem: knowing the needed care does not reveal whether a
   facility can provide it, how far it is, or what is actually documented.
2. Enter a clear referral request and constraints.
3. Show the three route options and the map.
4. Open one evidence casefile; show a missing or conflicting claim instead of
   hiding it.
5. Save or override the recommendation.
6. Reopen the saved plan, then show optional voice/handoff polish.

## What future agents should do

- Read this file first for product context.
- Read the original PDF before changing scope, making a requirement claim,
  selecting a Databricks service, or preparing the final submission.
- Prefer the narrow golden path over broad, unsupported healthcare features.
- Preserve evidence links, uncertainty, and user approval throughout the
  product.
