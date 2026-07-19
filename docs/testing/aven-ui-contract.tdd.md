# Aven UI contract: TDD evidence

## Purpose

Provide a stable backend façade so an independently developed UI can replace
`app.py` without copying business rules or creating merge conflicts.

## RED/GREEN evidence

- RED command: `.venv/bin/python -m unittest apps/referral-copilot/tests/test_ui_contract.py -v`
- RED result: intended `ModuleNotFoundError: No module named 'src.ui_contract'`
- GREEN command: the same targeted test command
- GREEN result: 8 tests passed
- Standard-library trace coverage: `src.ui_contract` 83.8%

## Guarantees

| Guarantee | Test type | Result |
|---|---|---|
| Confirmed request returns the stable UI plan shape | Integration | PASS |
| Emergency returns no ordinary options | Safety integration | PASS |
| Travel labels never claim a live fare | Unit/integration | PASS |
| Save, list, and reload match the UI handoff calls | Persistence integration | PASS |
| Overrides remain separate from source-backed option evidence | Safety/persistence | PASS |
| Feedback accepts only bounded statuses and does not mutate plans | Safety/persistence | PASS |
| Service status exposes no credential value | Security | PASS |
| Unsupported language fallback remains visible | Localization | PASS |

The façade was added in new files and did not modify `app.py` or
`docs/ui-handoff.md`, preserving UI-owner priority and minimizing conflicts.
