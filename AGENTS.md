# Hack-Nation shared build brief

This is the shared source of truth for every agent working in this repository.
Keep the product focused, demoable, and honest. Update this file when a prompt,
track, sponsor requirement, or product decision is confirmed.

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
