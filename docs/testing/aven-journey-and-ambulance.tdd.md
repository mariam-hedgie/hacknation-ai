# Aven journey and ambulance workflow — TDD evidence

## Source decision

Journeys were confirmed by the product owner on 2026-07-19 and recorded in
`AGENTS.md`. They cover deadline-aware recommendations, no-key route links,
external ticket actions, evidence-gated ambulance help, labelled seeded
estimates, and typed multilingual fallback when voice is unverified.

## RED

Commit `fde226d` added the confirmed workflow and tests before production code.
The focused suite failed because `src.journey` did not exist, ambulance was not
a valid mode, the domain lacked required-arrival and journey fields, voice was
enabled by key presence alone, and the UI lacked the new actions.

## GREEN

`python3 -m unittest discover -s apps/referral-copilot/tests -q` passed 206
tests. `coverage run --source=apps/referral-copilot/src ...` reported 86% total
source coverage. `python3 -m compileall -q apps/referral-copilot` and
`git diff --check` passed.

| Guarantee | Test | Type | Result |
|---|---|---|---|
| Google Maps route URLs are encoded and contain no key | `test_journey.GoogleMapsUrlTests` | unit | PASS |
| Seeded journey and ambulance estimates are labelled and bounded | `test_journey.DemoEstimateTests` | unit | PASS |
| Hospital and Tavily phone states remain distinct | `test_journey.AmbulancePlanTests` | unit | PASS |
| Missing phones are never invented and emergency 112 stays separate | `test_journey.AmbulancePlanTests` | safety | PASS |
| Booking links come only from a fixed provider allowlist | `test_journey.TicketLinkTests` | security | PASS |
| Deadline feasibility can outrank convenience among supported matches | `test_domain.ShortlistTests` | unit | PASS |
| Voice stays hidden until explicitly enabled | `test_voice.VoiceTests` | configuration | PASS |
| Date, route, ambulance, and booking actions remain in the UI | `test_ui_contract_alignment` | integration contract | PASS |

## Known limits

The challenge data has no structured hospital address, coordinates, phone, or
website. Seeded route figures are not live, Tavily phones need source review,
and airline links do not prove that a matching flight exists. Real provider
adapters must populate journey time, cost, and arrival feasibility before the
live ranking may use those fields.
