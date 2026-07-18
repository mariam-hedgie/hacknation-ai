# Prompt for Claude: Data Legend ideation within the rules

Copy the text below into Claude together with these two files from this repo:

- `docs/data-legend-build-brief.md`
- `docs/reference/data-legend-original-brief.pdf`

---

You are a rigorous product strategist and hackathon design partner. Help us
develop an ambitious but buildable entry for the Hack-Nation Databricks Data
Legend challenge.

Treat the attached original PDF as the source of truth. The attached build
brief is an interpretation, not a replacement for the rules. If they conflict
or a detail is unclear, quote the relevant PDF requirement, say that it is
uncertain, and do not invent a rule.

Our provisional direction is `Aven`: a Referral Copilot that uses
messy Indian healthcare-facility records to create evidence-backed,
access-aware referral route options. A patient or primary-care clinician can
set urgency, budget sensitivity, travel tolerance, care need, and language;
the product compares a small set of options and exposes the supporting,
conflicting, or missing facility evidence. A user can save a plan or override
the ranking with a note.

We want ideas that are memorable and visually impressive, but not a generic
healthcare chatbot, a generic map, or a dangerous medical-diagnosis product.

Non-negotiable constraints:

1. Deploy a live Databricks App on Free Edition.
2. Select one primary mission; we are leaning Referral Copilot.
3. Use the supplied facility data and trace outputs to its facility text.
4. Make uncertainty, contradictions, and data gaps visible.
5. Persist user state such as notes, shortlists, overrides, or scenarios.
6. Never fabricate prices, eligibility, doctor availability, wait times,
   clinical outcomes, or medical diagnoses. Label unknowns clearly.
7. If using voice, it must collect a user-facing request and require the user
   to confirm the structured summary before it drives a recommendation.
8. We need a reliable 24-hour-hackathon vertical slice and a <90-second demo.

Please produce:

1. Three refined product concepts ranked from strongest to weakest. Each must
   be meaningfully different, still fit Referral Copilot, and include one
   memorable demo moment.
2. For the strongest concept, give a 60-90 second demo story, exact screens,
   data flow, and the minimum viable data model.
3. Separate features into: `required by the brief`, `high-value for judging`,
   and `defer unless time remains`.
4. Identify the top five ways this concept could violate the rules or become
   unsafe/unverifiable, with a concrete guardrail for each.
5. Give a 3- or 4-person team split and a 24-hour build sequence.
6. Suggest only Databricks components that materially help; do not recommend
   platform services merely because they sound impressive.
7. End with one concise product sentence in this form: `For [user], we turn
   [painful input] into [decision/action] using [AI], with [trust mechanism].`

Be opinionated. Prefer a narrow, fully working product that makes uncertainty
useful over a broad feature list.
