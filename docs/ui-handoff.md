# Aven UI handoff

## Purpose

Build the patient-facing Aven interface around one promise:

> **The right care route, with proof.**

For a patient, caregiver, or primary-care worker navigating Indian healthcare
access, Aven turns a *confirmed* care need into a small, actionable,
evidence-backed next-step plan. It is not a medical diagnosis product, a
price/availability guarantee, a clinical-quality rating, or a generic chatbot.

This is a build handoff for the UI owner. For product requirements, use
[`final-product-plan.md`](final-product-plan.md). If anything here conflicts
with the competition requirements, read
[`reference/data-legend-original-brief.pdf`](reference/data-legend-original-brief.pdf)
and follow that document.

## Who we are designing for

### Primary person: the access-constrained patient or caregiver

They may know the clinical need (for example, “cardiology,” “blood draw,” or
“refill”) but not the practical route. They could be travelling a long way from
Patna/Bihar, have a strict budget, be more comfortable in Hindi or Marathi,
and be anxious about wasting a day or money on an unsupported facility. They
may share a phone with family, have low data connectivity, and care far more
about **what to do now** than how the AI works.

Design for:

- a short attention window and plain language;
- low confidence with healthcare systems, without assuming low literacy;
- mobile-first use and a one-handed, high-contrast interaction;
- language choice: English, Hindi, Marathi; and
- a family member/clinician who needs a clear handoff rather than a chat
  transcript.

### Secondary person: the primary-care clinician or community worker

They use Aven to turn a known referral or a patient’s stated need into a
transparent route. They need to see the patient’s constraints, confirm that
the request is correct, inspect exact evidence, save an override/note, and
share a concise handoff. Do not make them retype information already in the
conversation.

### Demo moments to support

1. **Patna/Bihar:** a family has a documented cardiology referral; they can
   travel by train and need to minimize wasted travel/cost.
2. **Urban tradeoff:** a Delhi, Bengaluru, or Mumbai user chooses between a
   closer route and a stronger evidence-backed route.
3. **Trust moment:** a facility detail conflicts or is absent; Aven clearly
   says `Call first` or `We could not confirm this`, rather than pretending.

## Design principles

These are the applicable “taste” principles for the build: functional,
calm, legible, and intentionally restrained. The user should feel guided, not
processed by a healthcare dashboard.

1. **Action before explanation.** Every completed plan begins with `What to
   do next`; evidence is one tap away, never hidden.
2. **One decision per screen.** Intake asks a single task-specific question at
   a time. Use chips/sliders for constraints after an open answer. Avoid a
   giant form or an empty chat canvas.
3. **Human language, not system language.** Say `Call first`, `Bring this`,
   `What we could not confirm`, and `Why this option?`, not “confidence
   score,” “retrieval,” “rank,” or “LLM.”
4. **Uncertainty is a first-class visual state.** Unknown and conflicting
   information must look intentional and useful, not like an error. Never use
   green to imply that a hospital is medically “good.”
5. **User control is visible.** The user reviews an editable request before
   search; can change preferences; can choose an alternative; and can save an
   override with a note.
6. **Progressive disclosure.** Lead with the plan. Put literal source spans,
   ranking factors, conflicts, and technical activity in an expandable
   Evidence Receipt.
7. **Calm trust, not clinical drama.** Use one primary action per section,
   generous spacing, familiar icons, purposeful color, and short sentences.
   Avoid dense tables, gradients, fake maps, excessive card nesting, and
   motion that competes with reading.
8. **Accessible by default.** Never rely on color alone. Meet readable text
   contrast, keep touch targets at least 44 px, let all controls work by
   keyboard, label icons, preserve focus, and keep a text-only path when voice
   or maps fail.
9. **Truth stays separate.** User notes/preferences, dataset evidence, and
   external sources must have visibly distinct labels. A user report is not a
   facility fact.
10. **Build the reliable golden path first.** The app must remain useful with
    seed data/no maps/no voice. Voice, map, and lodging are enhancements, not
    a replacement for the care plan.

## Information architecture

```text
Welcome / language
  -> conversational task intake
  -> task-specific questions + constraints
  -> editable confirmation card
  -> action plan with 1–3 route options
     -> option detail / Evidence Receipt
     -> save, share, or override
  -> saved plans / reopen
```

The **required trusted-AI workflow** must be clear in the UI:

```text
User input -> editable AI summary -> source-grounded recommendation
-> user selects/overrides -> saved action plan + optional feedback
```

The activity/evidence panel should record input summary, sources/evidence
used, uncertainty status, selected output, and final user action. It need not
look like an engineering trace viewer.

## Screens and key components

### 1. Welcome / intake

**Goal:** make starting feel safe and fast.

- Header: `Aven` and tagline, with compact language selector (`English | हिंदी
  | मराठी`). Do not require account setup to demonstrate the flow.
- Short promise: `Tell us what you need. We will help you plan the next step
  with evidence from facility records.`
- Prominent text field plus optional microphone button. If voice is present,
  use it only to capture/transcribe; show the text for correction.
- Example chips: `I have a referral`, `Need a test`, `Need a refill`, `Need
  help planning a visit`.
- Persistent but quiet boundary: `Aven helps plan access to care. It does not
  diagnose or replace emergency care.`

**Do not:** begin with a map, city selector, long survey, or a visible model
confidence number.

### 2. Guided task intake

**Goal:** collect only what is necessary for the selected care task.

- One conversational question per step; keep already-captured answers visible
  as compact editable chips above the question.
- Use disclosure only when needed: `Why do we ask this?` can explain that
  travel/budget preferences change route ordering, not care quality.
- Constraint controls: location, urgency, travel tolerance, budget
  sensitivity, public/private preference, language/accessibility. Sliders need
  visible text endpoints and a current label—not an unlabeled number.
- For known referral/procedure, ask for the named specialty/service first.
- For refill, request medicine/formulation and current prescription/refill
  confirmation; do not surface dose-change suggestions.
- For lab, ask for the test/order and whether there is a clinician order.
- For symptom-first, show an unavoidable emergency-warning question before
  normal planning; after a non-emergency response, label any proposed first
  setting as `Please review`, not a diagnosis.

**Recommended component:** a small stepper with labelled stages `Tell us` →
`Confirm` → `Your plan`, rather than a chatbot where the user cannot see
progress.

### 3. Emergency interruption

**Goal:** stop ordinary ranking, not merely warn inside a message.

- Full-width high-priority panel: `Get urgent help now`.
- Give local emergency/contact and safe transport wording only if it has been
  approved/sourced. Otherwise: `Seek local emergency care now. Do not wait for
  a facility comparison.`
- Offer `Start a new non-urgent request` only after the emergency direction.
- Never show hospitals ranked by price/distance on this path.

### 4. Editable confirmation card

**Goal:** make AI extraction reviewable before it affects results.

Show a sentence plus editable fields:

> `You are looking for [cardiology] from [Patna], soon. You prefer [lower
> travel burden] and [public or either] facilities.`

- Each field has an edit affordance; preserve the original spoken/typed text
  in the activity panel, not the main view.
- Primary CTA: `Confirm and find routes`.
- Secondary CTA: `Edit request`.
- Include: `We use your confirmed request to compare documented facility
  options. We do not infer price, availability, or eligibility.`

### 5. Action-plan results (the main screen)

**Goal:** provide a practical next move in seconds.

The first viewport should contain:

- A `Best next step` heading and the selected/recommended facility name.
- One sentence that says what is documented, distance/route estimate when
  present, and a transparent price state.
- A `Do this now` checklist with 3–4 concrete steps: call official contact,
  ask whether service is currently available, bring referral/ID/reports, save
  or share.
- Primary CTAs: `Save plan` and `Share`; secondary `Why this option?`.

Below it, use exactly up to three clear route cards:

| Card label | Meaning | Required treatment |
|---|---|---|
| Best documented fit | strongest literal support for confirmed capability | Show documented evidence label and short reason. |
| Lower-burden route | closer or aligned to public preference, only when data supports it | Explain the tradeoff; do not call it cheaper without a fee. |
| Alternative to verify | potentially useful option with major gaps/conflicts | Visibly show `Call first` / unknowns before the CTA. |

Card anatomy:

```text
Badge + route label                  Evidence state icon + text
Facility name
One-sentence fit / reason
Distance and route state             Cost state
What to do next
[View plan]  [Why this option?]
```

**Evidence status palette/copy** (choose accessible contrast; never use colour
alone):

| Status | Exact patient-facing copy | Visual treatment |
|---|---|---|
| Supported | `Documented in facility records` | Calm blue/teal badge with check icon. |
| Conflict | `Details disagree — call first` | High-attention amber badge with alert icon. |
| Unknown | `We could not confirm this` | Neutral/slate badge with question icon. |
| External | `Official external source` | Link/source icon, URL and retrieval date. |
| User context | `You told us this` | Distinct outlined chip; never next to evidence check. |

Use the same exact words everywhere. Do not turn statuses into stars,
percentages, traffic-light quality scores, or “verified hospital” badges.

### 6. Route/access comparison (progressive enhancement)

- A compact comparison drawer/section can show travel mode: walk, car, cycle,
  motorbike; bus/train only when a provider returns it. Clearly label
  `Estimated route` and `Transit estimate — verify service`.
- Keep a text fallback alongside the map. A map is context, not the answer.
- Taxi: link out only and say availability/fare are not confirmed.
- Plane: only an honest long-distance flag; no invented itinerary/price.
- Lodging: show `Nearby lodging — availability/rate not confirmed` only when
  a supported Places response exists.
- `Busy hours`: show official opening hours only; never represent crowding or
  “best time” without a valid source.

### 7. Evidence Receipt

**Goal:** win the Data Legend trust test without overwhelming patients.

Use an expanding panel or detail page, not a modal that blocks the plan. It
must include:

- `Why this option?` plain-language ranking explanation: which selected
  constraints mattered and which did not have data.
- Exact source text/sentence, source field name, facility record identifier,
  and any conflicting text.
- `What we could not confirm` as a dedicated, easy-to-scan section.
- External source link and retrieval timestamp when used; clearly separate it
  from challenge-data evidence.
- `You told us this` section for user preferences/referral context.
- Compact activity log: `Request confirmed` → `Records checked` → `Option
  chosen/saved`; show no private raw health detail beyond what the user
  approved.

The renderer must only display literal source spans returned by the data
adapter. Never allow generated citations to be created in the UI.

### 8. Save, override, share, and reopen

- `Save plan` must show a durable success state (not only a toast): `Saved —
  reopen it from My plans.`
- `Choose this instead` opens a short optional note: `Why does this route work
  better for you?` This is an override, not feedback that changes facility
  truth.
- `Share` produces a short, readable action-plan handoff: confirmed need,
  option selected, call/checklist, evidence status, and unknowns. Do not share
  a raw chat transcript by default.
- `My plans` lists saved plan title, city, care task, selected facility, and
  update date. Reopening preserves the plan, note, and evidence states.
- Feedback comes after the decision: `Helpful`, `Needs correction`, `Not
  sure`, plus an optional note. For post-visit access reports use factual,
  bounded labels: `Service unavailable`, `Price differed`, `Accepted`, `Not
  visited`.

## UI-to-logic integration contract

Build the interface as a thin client of the existing domain/data adapters.
Do not put clinical, evidence, or ranking decisions in component code.

### Intake request

The UI collects an editable draft. It may call an extraction service, but it
must send a search request only after `user_confirmed: true`.

```ts
type IntakeRequest = {
  care_task: "known_referral" | "procedure" | "lab" | "refill" |
    "symptom_first" | "follow_up";
  confirmed_capability: string | null;
  location: string | { latitude: number; longitude: number } | null;
  urgency: "routine" | "soon" | "urgent" | "emergency";
  travel_tolerance: "low" | "medium" | "high";
  budget_sensitivity: "low" | "medium" | "high";
  facility_preference: "public" | "private" | "either" | "unknown";
  language_preference: string | null;
  medication_name?: string | null;
  has_current_prescription?: boolean | null;
  has_clinician_order?: boolean | null;
  emergency_warning_reported: boolean;
  user_confirmed: boolean;
};
```

Before results, handle the domain safety state:

| Logic state | UI behavior |
|---|---|
| `emergency` | Render the emergency interruption and stop ordinary results. |
| `confirm_care_setting` | Ask the user to review a possible first care setting; no facility search yet. |
| `incomplete_intake` | Return the user to the specific missing/invalid field with plain-language error text. |
| `proceed` | Render the action plan or honest no-documented-match state. |

### Shortlist response

The Databricks/demo adapter should return up to three `RankedOption`s. The UI
must receive, rather than invent, all evidence status, literal spans, unknowns,
ranking reasons/cautions, official contact/link, and route labels. Existing
local interfaces are in:

- [`apps/referral-copilot/src/domain.py`](../apps/referral-copilot/src/domain.py)
- [`apps/referral-copilot/src/demo_adapter.py`](../apps/referral-copilot/src/demo_adapter.py)

Required rendering rules:

- literal evidence must be displayable and match the supplied source text;
- a missing field is `not documented`, never a negative capability claim;
- a public facility is not automatically lower cost or eligible for a scheme;
- rank/reason copy cannot claim medical appropriateness or clinical quality;
- display cost, availability, appointment, crowding, reviews/outcomes, and
  accessibility only when the adapter explicitly supplies a supported status;
- data failures must leave the user with an honest fallback (`Call first`,
  saved demo state, or retry), not an empty white screen.

### Persistence calls

The UI needs these asynchronous interactions (exact transport can change):

```text
save_plan(confirmed_request, selected_option, next_steps)
save_override(plan_id, facility_id, note, selected_despite_rank=true)
save_feedback(plan_id, bounded_status, optional_note)
load_saved_plans(demo_user_id)
load_plan(plan_id)
```

Show optimistic progress only if failure is recoverable. On save failure, keep
the plan visible and offer `Try saving again`; do not tell the user it was
saved until Lakebase confirms it.

## Voice, language, and content rules

- Voice (ElevenLabs) is optional and cannot be the only path. Text entry and
  text read-back must work without an API key.
- Treat transcription as a draft. Show it in the confirmation card; let the
  user edit it before a search/ranking call.
- Translate navigation, safety copy, confirmation, status labels, and call
  checklist as approved strings—not uncontrolled live translations during the
  demo. Keep medical terms in English as well if that improves clarity.
- Keep copy concise, direct, and active: `Call before you travel`, not `It is
  recommended that you attempt to contact the facility.`
- Avoid claims like `best doctor`, `fastest appointment`, `lowest cost`, or
  `safe hospital` unless a supported field precisely establishes that narrow
  claim (the current plan says it does not).

## States the UI owner must build and test

1. Loading: explain what is happening (`Checking documented facility records`)
   without implying live availability.
2. Documented evidence: source span visible; plan actionable.
3. Conflicting data: `Details disagree — call first`; conflict is visible.
4. Unknown data: explicit `We could not confirm this` plus a call/check action.
5. No documented match: useful next action, not an empty result.
6. Emergency: ordinary ranking is blocked.
7. Voice/map/external-service unavailable: text-only plan still works.
8. Save success, save failure, override saved, and saved-plan reload.
9. Mobile narrow viewport, keyboard-only flow, and high-contrast review.

## Suggested build order

1. Implement the calm page shell, language switcher, and text-only known
   referral flow.
2. Complete **confirm → shortlist → Evidence Receipt → save → reopen** using
   the deterministic adapter.
3. Add unknown/conflict/no-match and emergency states; test them before visual
   polish.
4. Add the route/access comparison with its no-key fallback.
5. Add share/override/activity panel.
6. Add voice and translated read-back only after the text golden path is
   reliable.

## Definition of done for UI handoff

A new user can, in under 90 seconds, state a known care need, confirm their
constraints, understand three different route options, inspect proof and
unknowns for one, save/override it, and reopen the plan. They never need to
understand the AI architecture in order to know what to do next.

Before handing the UI to demo/pitch, verify the seven scenarios in
[`overnight-agent-runbook.md`](overnight-agent-runbook.md), including the
Patna referral, urban tradeoff, emergency, refill, lab, and save/reload flows.
