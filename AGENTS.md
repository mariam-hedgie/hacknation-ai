# Hack-Nation shared build brief

This is the shared source of truth for every agent working in this repository.
Keep the product focused, demoable, and honest. Update this file when a prompt,
track, sponsor requirement, or product decision is confirmed.

## Data Legend source material

For the Databricks Data Legend track, use
[`docs/data-legend-build-brief.md`](docs/data-legend-build-brief.md) for the
working product context and
[`docs/reference/data-legend-original-brief.pdf`](docs/reference/data-legend-original-brief.pdf)
for the official source. If requirements, rubric, eligible technology, or
scope are unclear or contested, read the PDF and follow it over any summary.

The selected final product direction is documented in
[`docs/final-product-plan.md`](docs/final-product-plan.md). Follow it for
feature priorities, conversational-intake guardrails, and the patient-facing
experience; defer to the original PDF if it conflicts with the challenge.
The public product name is **Aven**; use it in user-facing copy, pitch,
screens, and documentation. Keep technical deployment identifiers separate
unless a deployment naming decision is explicitly confirmed.

Use [`docs/databricks-execution-plan.md`](docs/databricks-execution-plan.md)
for the Databricks implementation sequence, data contracts, deployment gates,
and GitHub-to-Databricks synchronization rules. Do not commit challenge data,
patient data, or credentials.

Hand the Databricks owners [`docs/databricks-team-handoff.md`](docs/databricks-team-handoff.md).
It contains their platform setup steps, owned deliverables, app skeleton,
data contracts, and integration handoff to the rest of the team.

For the final 15-hour build sequence, feature truth labels, mapping provider
choice, and agent-wave handoffs, follow
[`docs/overnight-agent-runbook.md`](docs/overnight-agent-runbook.md).

For UI implementation or a Claude design pass, use
[`docs/ui-handoff.md`](docs/ui-handoff.md). Preserve its patient-first action
hierarchy, exact uncertainty wording, mobile/accessibility constraints, and
thin-client boundary; UI code must not invent ranking or evidence claims.

## What Hack-Nation appears to reward

Build a working, focused AI product rather than a broad "AI assistant." The
event is a 24-hour global sprint, and the published judging signal is
**Energy**. Visible execution, a confident narrative, and a polished demo can
matter disproportionately.

Past Hack-Nation projects show a consistent pattern:

- **Atlas**: transformed a short phone conversation into a credible,
  verifiable skills credential.
- **CareMap AI**: validated facility claims and produced trust scores from
  messy healthcare data.
- **Sonara**: created evidence-based skill profiles, confidence scores, and
  job matching.

The common shape is: one narrow input, non-trivial AI reasoning, a trusted
concrete output, and an obvious beneficiary.

## Product design principles

1. Solve one costly or frustrating workflow for one specific user.
2. Do not build a generic chatbot for a domain.
3. Make AI essential: the product should be materially weaker without it.
4. Build an AI decision-and-action workflow:

   `messy input -> AI extracts/reasons -> evidence and confidence -> user approval -> action/output`

5. Make trust visible with sources, confidence or uncertainty, and a human
   approval step.
6. Make sponsor technology central to the experience, never decorative.
7. Add exactly one memorable capability: multimodal intake, an agent action,
   evidence verification, personalized reasoning, or live collaboration.
8. Prefer a narrow, complete vertical slice over a larger collection of
   disconnected features.

## Fast idea filter

Choose a track/idea only if it has all or nearly all of the following:

- A named user with a real problem today.
- One impressive end-to-end result that can be shown in under 90 seconds.
- An AI capability that is genuinely necessary.
- Public, sample, or immediately-creatable demo data.
- Clear sponsor alignment.
- A useful edge such as verification, personalization, multimodal input, or
  action-taking.

## Track-selection strategy: competitive, not merely interesting

Prefer the track with the **lowest expected competition where this team has a
real advantage**. Do not choose a track only because it is familiar or has a
large sponsor name.

For each track, score the following before committing:

| Factor | What to prefer |
|---|---|
| Expected participation | Fewer confirmed teams or lower visible hype; use organizer data where available, otherwise label this as an estimate. |
| Team advantage | A domain insight, relevant technical skill, credible demo data, or a notably stronger ability to execute the sponsor stack. |
| Buildability | A complete, reliable demo within the sprint—not a research project. |
| Distinctiveness | A solution unlikely to converge on the obvious chatbot/dashboard most teams will build. |
| Sponsor fit | A use of the sponsor technology that is necessary and easy for judges to recognize. |

Use this decision rule: choose the track with the best combined score for
**team advantage + buildability + distinctiveness**, then break close ties in
favor of lower expected participation. Never invent team counts: record the
source if an organizer provides them, or explicitly mark the assessment as a
proxy (for example, Discord activity, waitlist interest, or prompt breadth).

Avoid overcrowded tracks unless the team has an unusually strong, concrete
edge that can be demonstrated immediately.

Before implementation, write and agree on this sentence:

> For [specific user], we turn [painful input] into [specific decision/action]
> using [AI capability], with [trust mechanism].

## Build priorities

- First 45 minutes after prompt release: read rules together, generate only
  three ideas, score them, and commit to one by minute 45.
- First 3 hours: ship a deployed, working golden path.
- Build the golden path together before dividing into independent features.
- Keep the experience deterministic: seeded accounts, prefilled forms, sample
  data, and a fallback result. Avoid fragile live dependencies in the demo.
- Include loading and error states, evidence cards, confidence labels, and an
  honest limitations note.
- Document the problem, architecture, AI role, setup, demo steps, and future
  work in the README.

## Demo and pitch standard

The first meaningful output must appear within 90 seconds. Prepare a backup
screen recording before submission. A clear, rehearsed demo can beat a more
ambitious but confusing build.

Pitch structure:

> [User] loses [time/money/safety] because [specific workflow]. Today they
> have to [bad workaround]. We built [product]. In 60 seconds, watch it turn
> [input] into [verified actionable output]. The AI does [specific nontrivial
> task], while [guardrail] keeps the user in control. This can scale because
> [short reason].

## Required decision checkpoint: trusted AI workflow

After every meaningful product choice (track, problem, user, input, AI
capability, evidence source, action, or demo flow), the agent must pause and
show how that choice fits this lightweight workflow:

`user input -> AI reasoning with evidence -> recommendation -> user feedback/approval -> trusted action`

The agent must explicitly ask the user to confirm or adjust the choice before
making the next dependent decision. Keep this checkpoint concise and include:

- **Trace:** what will be recorded for this AI decision (input, output,
  sources/tools, confidence, and final user action).
- **Feedback:** how a user can mark the result helpful/incorrect and provide a
  correction when relevant.
- **Evaluation:** which 5–10 seeded cases will test accuracy, evidence quality,
  safety, usefulness, and actionability.
- **Guardrail:** what explanation, uncertainty label, and approval step keeps
  the user in control.

For the hackathon, implement this as a lightweight in-product activity/evidence
panel plus feedback controls and deterministic sample cases. Do **not** spend
time adopting MLflow, Unity Catalog, or a full observability platform unless a
sponsor track explicitly requires it.

## Tavily: web evidence for agent workflows

Tavily is installed as the project's agent-oriented web research SDK
(`@tavily/core`). Use it only when the product needs current, public web
evidence that is not already present in the challenge dataset or a user-provided
source.

Use the smallest suitable endpoint:

- **Search:** discover current, public sources for a focused factual question.
- **Extract:** retrieve clean content from a known relevant URL.
- **Map or crawl:** only for a narrowly scoped, public official domain when the
  workflow needs more than one page; set a clear page/domain limit first.
- **Research:** only for a deliberate, multi-source research task where a
  short, attributable synthesis is the user-facing outcome.

For Data Legend, Tavily may cross-check a facility's supplied public source URL
or an official standard; it must never replace the dataset's row-level evidence.
Clearly label external evidence with its URL and retrieval time. If sources
conflict or evidence is absent, lower confidence or return an explicit
"unknown" state instead of inferring a capability.

Do not send personal data, application documents, credentials, private URLs,
or raw health information to Tavily. Do not use it to infer eligibility,
protected traits, medical treatment, or a fact that requires a primary source
you have not obtained. Prefer a basic/fast search for routine checks and use
advanced search only when the expected evidence gain justifies the extra credit.

Configuration: each developer creates a local `.env` from `.env.example` and
sets `TAVILY_API_KEY`. Never commit a real API key. The Hack-Nation guide says
the free account includes 1,000 monthly credits and the event code
`HackNationJuly` redeems the Project plan for two months; confirm availability
in the Tavily dashboard before relying on it.

## ElevenLabs: voice intake, not hidden decision-making

Use ElevenLabs only for an explicit, user-facing voice interaction: collect a
planner's spoken request, present an accessible spoken summary, or conduct the
voice negotiation flow required by the ElevenLabs challenge. The user must be
able to review and correct the structured information produced from speech
before it drives a search, ranking, or action. Keep `ELEVENLABS_API_KEY` on the
server; never embed it in client code or commit it to the repository.

## Suggested team ownership

- **Product lead / pitcher:** framing, user flow, rubric, submission, pitch.
- **AI / agent engineer:** model calls, retrieval or tools, evaluation, magic
  moment.
- **Full-stack engineer:** deployed vertical slice and integrations.
- **UX / demo engineer:** interface, demo data, loading/error states,
  screenshots or video.

One person must explicitly own the final submission. These are ownership areas,
not silos: pair on the core user flow first.

## Guardrails for agents

- Optimize for a reliable, compelling demo, not feature count.
- Do not invent claims, metrics, sources, confidence values, or sponsor support.
- Label sample/seeded data clearly when it is used.
- Preserve a human decision point for consequential recommendations or actions.
- Check the official rules, challenge track, sponsor requirements, and
  submission requirements as soon as they are available; those take precedence
  over this brief.
