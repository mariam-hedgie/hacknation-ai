# Aven local app: TDD evidence

## Source and journeys

The user journeys came from [`../final-product-plan.md`](../final-product-plan.md)
and [`../overnight-agent-runbook.md`](../overnight-agent-runbook.md):

1. A person confirms a known care need before facility options appear.
2. Emergency and incomplete/refill-without-prescription paths stop ordinary ranking.
3. Facility claims retain literal evidence, conflicts, and unknown fields.
4. Travel modes state what the configured provider can and cannot supply.
5. English, Hindi, and Marathi safety/core copy works without live translation.
6. Saved plans and feedback survive in session fallback when persistence is unavailable.
7. A no-key Streamlit path loads, reaches confirmation, and renders three labelled demo cards.

## RED and GREEN record

| Behavior | RED evidence | GREEN evidence |
|---|---|---|
| Confirmed request gate | `test_app_logic.py` failed with missing `src.app_logic` | 5 app-logic tests pass |
| Maps truth adapter | `test_maps.py` failed with missing `src.maps` | 12 maps tests pass |
| Databricks/persistence adapter | `test_databricks_adapter.py` failed with missing module | 12 adapter tests pass |
| Localization and voice boundary | `test_localization.py` failed with missing module | 16 localization tests pass |
| Streamlit golden path | Dynamic confirmation-to-result test exposed missing widget state | Stable confirmation/result and emergency AppTests pass |
| Secret-safe ElevenLabs check | Node test failed with missing check library | 4 Node tests pass, including network/error redaction |

No Git checkpoint was created at each RED/GREEN boundary because concurrent
agents shared the same working tree. This report preserves the exact evidence
before the final combined commit.

## Test specification

| What is guaranteed | Test target | Type | Result |
|---|---|---|---|
| Unconfirmed, incomplete, emergency, and unsafe refill requests return no option cards | `test_app_logic.py`, `test_domain.py` | Unit/integration | PASS |
| Documented evidence requires a literal cited span and conflicts outrank positive badges | `test_domain.py`, `test_databricks_adapter.py` | Unit/integration | PASS |
| SQL user values are bound parameters and never concatenated into the statement | `test_databricks_adapter.py` | Security/integration | PASS |
| Session fallback saves copy-isolated plans and append-only feedback | `test_databricks_adapter.py` | Integration | PASS |
| Google, ORS, and offline modes expose honest route/comparison labels and no live fare claim | `test_maps.py` | Unit | PASS |
| English/Hindi/Marathi strings, visible fallback, and untrusted transcript validation work offline | `test_localization.py` | Unit/security | PASS |
| Streamlit renders the intake, confirmation, result cards, and blocking emergency interruption | `test_streamlit_app.py` | UI integration | PASS |
| ElevenLabs credential errors never expose the credential or raw network exception | `elevenlabs-check-lib.test.mjs` | Unit/security | PASS |

## Commands and results

```text
.venv/bin/python -m unittest discover -s apps/referral-copilot/tests -v
Ran 64 tests ... OK

npm test
4 tests passed, 0 failed

.venv/bin/python -m py_compile apps/referral-copilot/app.py apps/referral-copilot/src/*.py
exit 0

curl http://127.0.0.1:8501/_stcore/health
ok

npm audit --omit=dev
found 0 vulnerabilities
```

The standard-library trace coverage run reported:

| First-party module | Line coverage |
|---|---:|
| `app.py` | 83.2% |
| `src.app_logic` | 94.6% |
| `src.databricks_adapter` | 87.7% |
| `src.demo_adapter` | 100.0% |
| `src.domain` | 86.4% |
| `src.localization` | 100.0% |
| `src.maps` | 95.6% |

## Known gaps and honest integration state

- Databricks workspace tables, app identity, Lakebase durability, and the final
  deployed URL are external-team handoffs and were not live-tested here.
- The local app displays seeded cards; it does not present them as challenge-data facts.
- The existing ElevenLabs credential reached the API but returned HTTP 401 on
  2026-07-19. Typed input works; voice should not be demoed as live until a new
  key passes `npm run check:elevenlabs`.
- Google/ORS requests are intentionally not executed by the adapter yet; the
  UI exposes provider capability and fallback truth labels only.
- Streamlit AppTest retains disappeared form widgets across an explicit
  `st.rerun`; the test therefore checks the confirmation and result states in
  separate harness instances using the same confirmed outcome. The real local
  Streamlit server health endpoint passed.
