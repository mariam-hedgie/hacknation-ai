# Databricks handoff and live-mode TDD evidence

## Journey

As the Databricks deployment owner, I need the app to identify complete AI
Search configuration as live evidence so the submitted UI does not incorrectly
label authenticated challenge-data results as demo data.

## RED

Command:

```bash
.venv/bin/python -m unittest apps/referral-copilot/tests/test_backend_config.py -q
```

Observed failure: a complete Vector Search endpoint/index pair returned `demo`
because `BackendConfig.mode()` also required an unused serving endpoint.

## GREEN

The mode now requires the complete endpoint/index pair and does not require an
unrelated serving endpoint. Partial configuration remains `demo`.

Verification:

- targeted backend/deployment tests: 3 passed;
- complete Python suite: 240 passed;
- Node UI/deployment contracts: 8 passed;
- React production build: passed;
- frontend lint: passed with existing Fast Refresh warnings only.

| Guarantee | Test | Type | Result |
|---|---|---|---|
| Complete AI Search configuration activates live evidence mode | `test_backend_config.py` | Unit | PASS |
| Partial AI Search configuration stays demo | `test_backend_config.py` | Unit | PASS |
| Deployment references the exact AI Search endpoint and App resource key | `test_deployment_config.py` | Contract | PASS |
| Searchable table preserves embedding text and raw receipt fields | `test_vector_search.py` | Contract | PASS |

No checkpoint commits were created because the product owner explicitly asked
to review and commit all changes at the end.
