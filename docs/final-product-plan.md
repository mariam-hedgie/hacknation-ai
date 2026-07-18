# Aven: final product plan

## Product in one sentence

**For patients and primary-care teams navigating Indian healthcare access, Aven turns a spoken or typed care request into a saved, evidence-backed next-step plan, using transparent facility-data reasoning and human confirmation.**

Tagline: **The right care route, with proof.**

## Source of truth and scope

This plan implements the Databricks Data Legend **Referral Copilot** mission.
Read these before changing requirements or scope:

- [`reference/data-legend-original-brief.pdf`](reference/data-legend-original-brief.pdf) - official challenge source of truth.
- [`data-legend-build-brief.md`](data-legend-build-brief.md) - detailed rule interpretation and technical guidance.

The product is decision support for access to care. It is **not** a diagnostic
tool, medical prescriber, clinical-quality rater, price guarantee, real-time
scheduler, or eligibility decider.

## The user promise

Someone may not care how the AI works. They need to know:

1. What should I do next?
2. Where can I go?
3. What can I confirm before I spend time and money travelling?
4. What should I bring, ask, or share with my family or clinician?

The first screen therefore gives an actionable plan in plain language. The
underlying evidence is never hidden, but is progressively disclosed through
`Why this option?` and `What still needs checking?`.

## Primary interaction: conversational intake

The user can type or speak naturally in a tested supported language. ElevenLabs
is an accessibility layer for recording/transcribing and reading the approved
plan aloud; it must not make hidden decisions.

Example opening:

> "I have stomach pain and need to know whether I should go somewhere today."

> "My doctor said I need a cardiology visit. I can travel by train but cannot
> spend much."

> "I have a prescription and need a refill."

> "I need a blood draw near my home."

The system identifies the **care task**, then asks only the smallest set of
task-specific questions. It shows the extracted request as a structured,
editable summary. The user or clinician must confirm it before any facility
search, ranking, route plan, or handoff is created.

```text
Spoken or typed request
  -> identify task and possible urgency
  -> ask targeted questions
  -> show editable structured summary
  -> user / clinician confirms
  -> retrieve evidence and create next-step plan
  -> save, share, or override plan
```

## Care-task flows

### A. Known referral, specialty, or procedure

Use this when the user has already been told what care they need, for example
`cardiology`, `blood test`, `dialysis`, `maternity care`, or a named procedure.

Ask for:

- specialty/capability or the procedure as written on the referral;
- referral information or a document summary, if they choose to share it;
- location, urgency, travel tolerance, and budget sensitivity;
- public/private preference, language, and accessibility needs if relevant.

Output:

- a small evidence-backed facility shortlist;
- a recommended next action and an alternative route;
- official contact/appointment link only when a supported source provides it;
- a `What to ask before travel` checklist;
- a shareable referral handoff.

### B. Medication refill or pharmacy need

This is **not** a prescription-writing flow. It helps someone find a supported
next step for an existing medication need.

Ask for:

- medicine name and formulation, if known;
- whether they have a current prescription/refill instruction;
- enough remaining medication to establish time sensitivity;
- location and whether delivery or travel is possible;
- an optional photo/text summary of the prescription, reviewed by the user.

Output rules:

- Never recommend changing a dose, stopping a medicine, substituting a drug,
  or bypassing a prescription requirement.
- If the challenge data includes pharmacy/service evidence, show only those
  source-backed options. If it does not, give an actionable, safe fallback:
  contact the prescriber/clinic, use an official pharmacy finder if integrated,
  or call a known local pharmacy.
- Any pharmacy availability, stock, delivery, or price is `not confirmed`
  unless a valid source or integration establishes it.

### C. Lab or blood draw

Ask for:

- test or order, if known;
- whether a clinician has provided an order/referral;
- location, timing constraints, mobility/access needs, and travel tolerance;
- whether home collection is desired, only if the evidence/data supports it.

Output:

- supported facilities/labs, or an explicit `not documented` state;
- official contact/booking source only when available;
- a verification checklist: test availability, order requirement, fasting or
  preparation instructions only when provided by the official facility source.

### D. Symptom-first request

Example: `I have tummy pain. How much will a consultation cost?`

The product must not diagnose or promise that a specific specialist is needed.
It performs a minimal safety-first intake:

1. Ask whether there are predefined emergency warning signs.
2. If a warning sign is reported, stop ordinary ranking and direct the user to
   urgent/emergency help and an immediate contact/transport action.
3. Otherwise say that it can help plan a possible first care setting, not
   diagnose the cause.
4. Ask the user to confirm the proposed care setting before facility search.
5. Show consultation cost only when sourced; otherwise label it `not
   confirmed` and give a call script.

The UI must make the emergency branch unavoidable; do not bury it in a chat
message or rely on the model alone to detect it.

### E. Follow-up, appointment, or access question

Use this when the user already has a facility or doctor in mind.

Ask for the named facility/doctor, required specialty/procedure, desired date,
and travel constraints. Show official appointment/phone information if present
in an approved source. Never infer real-time clinician availability. If no
official appointment data exists, show `Call to confirm` rather than a fake
slot or optimal-time claim.

## Conversational design rules

- Ask one plain-language question at a time; explain why only if needed.
- Do not make users repeat information the conversation already captured.
- Prefer choices/chips after an open response to reduce typing burden.
- Always read back a concise, editable summary before search.
- Let the user stop, save, share, or switch to text at any time.
- Use familiar labels: `What to do next`, `Call first`, `Bring this`, `What we
  could not confirm`.
- Never expose an LLM confidence percentage as though it represents clinical
  correctness.

## Search and planning inputs

After confirmation, Aven creates a transparent planner query:

```text
care task / confirmed capability
location
urgency
travel tolerance
budget sensitivity
public/private preference
language and accessibility preference
known referral or prescription context
```

For the demo, `budget sensitivity` may only change ranking based on fields the
dataset actually contains, such as facility type. It must not imply a price
when there is no supported fee data. Similarly, language is `documented`,
`not documented`, or `user preference`; lack of a text mention does not mean a
facility cannot provide that language.

## Patient-facing result: the action plan

The top of every result is understandable without opening the evidence layer.

```text
Best next step

City Hospital, Patna
Cardiology is documented in this facility's records.
18 km away. Travel estimate is a demo estimate.
Consultation price: not confirmed - call before leaving.

Do this now
1. Call the official number.
2. Ask whether the needed service is currently available.
3. Bring the referral, ID, and prior reports.
4. Save or send this plan to a family member or clinician.

[Save plan] [Share] [Why this option?]
```

Show three deliberately different options when enough evidence exists:

1. **Best documented fit** - strongest source support for the confirmed need.
2. **Lower-burden route** - shorter travel or public-facility preference when
   the data supports that comparison.
3. **Alternative to verify** - useful option with important gaps prominently
   shown.

Do not claim a single objectively best hospital.

## The evidence layer: Data Legend's core value

`Why this option?` opens an **Evidence Receipt**:

- exact source sentence(s) and source field(s) supporting a capability;
- any conflicting facility text;
- what is not documented;
- ranking factors that the user selected;
- a clear label: `data corroboration`, not medical quality or safety.

Evidence statuses:

| User-facing label | Internal meaning |
|---|---|
| Documented in facility records | Source text supports the displayed claim. |
| Details disagree - call first | Relevant records conflict. |
| We could not confirm this | The data does not establish the claim. |
| Official external source | Separately supported, linked, and retrieval-dated. |
| You told us this | User-provided context; never treated as facility evidence. |

Before displaying a generated citation, verify that the cited text literally
exists in the stored source field. Discard unsupported generated citations.

## Persistence and feedback

The brief requires useful persisted state. At minimum, a seeded demo user can:

- save a care plan;
- shortlist a facility;
- add a note;
- override the ranking and explain why;
- reopen the saved plan after reload;
- optionally report access feedback: `service unavailable`, `price differed`,
  `accepted`, `not visited`.

Keep user notes and overrides separate from source-derived facility evidence.
They can inform a user plan, but must never silently modify a trust score.

## Data model

```text
facilities_raw                  # challenge data, immutable source
facility_claims_evidence        # sourced claim and literal supporting span
facility_trust_assessment       # corroboration, conflicts, missing fields
planner_queries                 # confirmed user constraints only
saved_care_plans                # chosen options and editable plan content
shortlists                      # saved candidate facilities
user_notes_overrides            # human decision context, separate from evidence
access_feedback                 # optional post-visit access outcomes
```

Suggested persistence fields:

```text
saved_care_plans:
  plan_id, demo_user_id, query_id, selected_facility_id, care_task,
  next_steps, user_language, created_at, updated_at

user_notes_overrides:
  override_id, plan_id, facility_id, user_note, selected_despite_rank,
  created_at
```

## Minimal Databricks architecture

```text
Challenge CSV / source data
  -> Delta source table
  -> source-grounded evidence extraction and span verification
  -> transparent ranking function
  -> Databricks App: conversation, results, Evidence Receipt, save/reopen
  -> persisted plan and feedback tables
```

Use Databricks Apps as the sponsor centerpiece. The challenge mentions tools
such as Agent Bricks, Genie, MLflow 3, Mosaic AI Vector Search, and Lakebase;
use only services that materially enable the deployed vertical slice. Do not
let stack complexity prevent the core app from working.

Recommended priority:

1. Delta tables + Databricks App + durable saved-plan table.
2. Source-grounded evidence extraction and literal-span verification.
3. Transparent ranking and Evidence Receipt.
4. Voice input/output with confirmation.
5. Optional MLflow trace viewer, vector search, map, or validator pass.

## Required versus stretch scope

### Must ship

- live Databricks App on Free Edition;
- one Referral Copilot golden path using the supplied data;
- conversational or typed intake with editable confirmation;
- one supported known-care/referral flow;
- evidence-attached shortlist and `What we could not confirm` panel;
- save/note/reopen persistence;
- source-grounded, non-diagnostic safety copy;
- README, reproducible setup, and seeded demo scenarios.

### High-value if time allows

- voice intake and read-back in 2-3 tested languages;
- urgency, travel, and budget-preference sliders with transparent effect on
  ranking;
- symptom-first safety flow;
- prescription/refill and lab-order task routing, only if source data supports
  the downstream options;
- map with `has evidence`, `conflicting`, and `insufficient data` states;
- MLflow reasoning trace viewer;
- deterministic contradiction validator.

### Do not build in the hackathon unless a verified integration already works

- all-India real-time transit, hotel, pharmacy stock, or doctor schedules;
- exact treatment cost prediction;
- insurance or government-scheme eligibility decision;
- diagnosis, triage replacement, medication changes, or prescribing;
- unverified reviews/outcomes used as clinical-quality claims.

## Team split and build order

### Four people

| Owner | Accountable for |
|---|---|
| Product/demo lead | Scope, rubric, safety copy, demo script, final submission |
| Data/Databricks engineer | Delta ingestion, evidence tables, ranking, persistence |
| AI engineer | Conversational extraction, confirmation card, span verification, guardrails |
| App/UX engineer | Databricks App, action-plan UI, Evidence Receipt, voice and demo polish |

### 24-hour sequence

1. **Hours 0-2:** Inspect real fields; choose one care capability and two
   seeded scenarios. Define evidence statuses and emergency language.
2. **Hours 2-6:** Load data, create evidence table, and scaffold the app.
3. **Hours 6-10:** Complete confirmed referral -> shortlist -> Evidence Receipt
   -> save/reopen path.
4. **Hours 10-14:** Add conversational intake and exact-span verification.
5. **Hours 14-18:** Add clear action-plan copy, ranking controls, and a second
   scenario; test every unknown/conflict state.
6. **Hours 18-21:** Add voice or map only if the golden path is reliable.
7. **Hours 21-24:** Deploy, record backup demo, rehearse, document, submit.

## Demo story

> A family has been told a relative needs a cardiology consultation. They can
> travel by train but cannot risk a costly, wasted trip. They speak their need,
> confirm the plan, and Aven returns three understandable routes. They choose
> the best documented fit, see what the data proves and what it cannot prove,
> save the plan, and share the call checklist. Aven does not pretend to know
> everything - it helps them leave home with a plan.

## Evaluation and safety checklist

Use 5-10 seeded tests including documented evidence, conflicting evidence,
missing data, an override, reload persistence, rural/urban tradeoffs, and an
urgent symptom branch. For each test verify:

- every citation literally matches source text;
- missing data stays unknown rather than becoming a negative claim;
- chat asks targeted questions and requires confirmation;
- the action plan is useful without viewing AI details;
- persisted notes remain separate from facility evidence;
- no result invents price, availability, eligibility, diagnosis, or outcome.
