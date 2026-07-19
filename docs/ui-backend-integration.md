# Aven UI/backend integration boundary

## Ownership rule

The UI owner has priority over all visual and interaction decisions in
[`ui-handoff.md`](ui-handoff.md) and owns
[`apps/referral-copilot/app.py`](../apps/referral-copilot/app.py). Backend work
must not reformat, restyle, or restructure that file while their UI branch is
active.

The UI should import only the stable façade in
[`src/ui_contract.py`](../apps/referral-copilot/src/ui_contract.py). It should
not reproduce safety, evidence, ranking, localization, travel, or persistence
rules inside components.

## Stable usage

```python
from src.ui_contract import AvenUiBackend

backend = AvenUiBackend(st.session_state)

result = backend.confirm_and_plan(confirmed_request)
if result.safety_branch == "emergency":
    render_emergency_interruption(result.message)
elif result.safety_branch == "incomplete_intake":
    render_validation_errors(result.validation_errors)
elif result.safety_branch == "confirm_care_setting":
    render_care_setting_review(result.message)
else:
    render_plan(result.options)
```

The façade matches the handoff calls:

```python
backend.save_plan(
    confirmed_request,
    selected_option,
    next_steps,
    plan_id="demo-plan-1",
)
backend.save_override(plan_id, facility_id, note)
backend.save_feedback(plan_id, "needs_correction", optional_note)
backend.load_saved_plans("demo-user")
backend.load_plan(plan_id)
backend.travel_capabilities(["car", "bus", "train"])
backend.copy("review_and_confirm", "hi")
backend.service_status()
```

`service_status()` returns capability flags only and never credential values.
`travel_capabilities()` never supplies a live fare. User overrides and feedback
remain separate from facility evidence.

## Files the UI owner may replace freely

```text
apps/referral-copilot/app.py
future UI-only assets/styles/components
```

## Files to treat as backend contracts

```text
apps/referral-copilot/src/ui_contract.py
apps/referral-copilot/src/app_logic.py
apps/referral-copilot/src/domain.py
apps/referral-copilot/src/databricks_adapter.py
apps/referral-copilot/src/maps.py
apps/referral-copilot/src/localization.py
apps/referral-copilot/src/demo_adapter.py
```

If a UI requirement cannot be expressed through `AvenUiBackend`, request a
small additive method in `ui_contract.py`; do not edit the lower-level modules
or duplicate their logic in `app.py`.

## Low-conflict merge sequence

1. UI owner rebases or pulls the latest `mariam` branch before the final UI pass.
2. UI owner changes only `app.py` and new UI-only assets.
3. Backend owner changes only `src/`, its tests, and backend documentation.
4. Run the UI-contract and complete suites before merge:

   ```bash
   .venv/bin/python -m unittest apps/referral-copilot/tests/test_ui_contract.py -v
   .venv/bin/python -m unittest discover -s apps/referral-copilot/tests -v
   ```

5. If `app.py` conflicts, accept the UI owner's version, then reconnect it to
   `AvenUiBackend`. Do not restore the older Streamlit layout wholesale.

## Acceptance checklist

- Confirmation occurs before `confirm_and_plan`.
- `emergency`, `incomplete_intake`, and `confirm_care_setting` block results.
- Option proof and unknowns come from the returned option—not UI-authored copy.
- Save success is shown only after `save_plan` returns.
- Overrides/feedback remain visibly labelled as user context.
- Typed input still works when voice is unavailable.
- Route, fare, transit, cost, availability, and eligibility labels follow the
  returned truth state.
- The UI owner's mobile, accessibility, language, and Evidence Receipt design
  remains authoritative.
