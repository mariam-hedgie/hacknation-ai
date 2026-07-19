# Aven planning and accessibility redesign — TDD evidence

Date: 2026-07-19

## Journeys covered

- A person enters concrete distance, transport, travel-budget, and care-budget
  limits without fighting a discrete slider.
- Missing price evidence stays visibly unknown instead of becoming a fabricated
  budget claim.
- Emergency help remains reachable throughout the flow.
- English, Hindi, and Marathi use the intended Aven brand rendering.
- A configured ElevenLabs client transcribes only after explicit third-party
  consent and returns editable text for review.
- A configured Tavily client receives only the facility name and confirmed
  service; returned pages remain external source candidates and cannot change
  ranking evidence.

## RED checkpoint

The tests were committed first as `4bdd6dc`. The focused run failed because
`src.preferences`, `src.voice`, and `src.web_evidence` did not exist, and the
UI still used discrete select sliders, decorative icons, and had no persistent
emergency/contact controls. Security follow-up tests also failed before URLs
with credentials/whitespace were rejected and before explicit voice consent
was present.

## GREEN checkpoint

Final local validation:

```text
153 Python tests passed
4 Node tests passed
Application-module coverage: 84% (1,374 statements, 218 missed)
compileall: passed
git diff --check: passed
merge-marker scan: passed
Streamlit startup: passed
/_stcore/health: ok
```

The full Python suite includes preference, domain filtering, localization,
voice-review, public-source normalization, UI-contract, persistence, security,
and Streamlit rendering tests.

## Boundaries that local tests do not prove

- The local Databricks path still uses seeded demo results when the live
  shortlist integration is unavailable.
- ElevenLabs is configured locally, but a real transcription request was not
  sent during this verification. Typed intake remains the fallback.
- Tavily is not configured in the current local `.env`; public-source discovery
  therefore cannot be live-tested here.
- Google sign-in is not configured. The deployed design uses Databricks OAuth;
  the local profile is not a production signup flow.
- Seeded rows do not contain verified doctor rosters, procedure prices, or
  travel fares. The UI must continue to say unknown until an attributable
  source provides a number.
