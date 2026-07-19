# Aven live intake and planning UI — TDD evidence

## Red

Commit `8ae3f44` introduced contract tests for review-gated OpenAI intake,
bounded ElevenLabs uploads, Tavily phone candidates, Google-compatible travel
modes, persistent My plans navigation, account explanations, equal-height task
cards, and exact conflict copy. The focused suite failed because `src.nlp`,
phone extraction, the upload limit, the new travel mappings, and the UI copy
did not yet exist.

## Green

The implementation adds those boundaries without making live service claims
when a key or provider is absent.

- `python3 -m unittest discover -s apps/referral-copilot/tests -q`: 167 passed.
- `coverage run --source=apps/referral-copilot/src ...`: 84% total source
  coverage.
- `python3 -m compileall -q apps/referral-copilot`: passed.
- Synthetic OpenAI Responses call: passed and returned a review-required
  structured draft.
- ElevenLabs credential check: integration reached ElevenLabs, but the current
  credential returned `401 Unauthorized`; live voice remains visibly
  unavailable until the key is replaced or permitted for Speech-to-Text.
- Tavily configuration check: no real key is currently configured, so the UI
  preserves the no-external-lookup fallback.

## Security and trust checks

- API keys remain server-side environment variables.
- OpenAI receives only explicitly submitted intake text and uses `store=False`.
- ElevenLabs requires consent and rejects audio larger than 10 MiB before an
  upload attempt.
- Tavily receives only the facility name and confirmed service, validates
  result URLs, and labels links and phone numbers as unverified candidates.
- Model output remains an editable draft and cannot trigger search or ranking
  until the user confirms the form.
- Dynamic values rendered through custom HTML are escaped.
