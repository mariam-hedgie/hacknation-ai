# Login and persistence security: TDD evidence

## User journeys

- As a signed-in Databricks App user, I can reopen my saved decision without
  another user being able to access it by guessing the plan ID.
- As a privacy-conscious user, saving a shortlist does not retain my raw login,
  conversation, medication, location, transcript, or voice data.
- As a user, I can delete my saved plan and its feedback without affecting
  another user's records.
- As a deployer, missing identity/secret configuration fails closed rather than
  silently creating a shared demo account.

## RED evidence

Tests were committed first in `8a089b5`. The first targeted run executed the new
tests and failed for the intended missing behavior:

```text
ModuleNotFoundError: No module named 'src.auth'
TypeError: PersistentSqlPlanStore.__init__() got an unexpected keyword argument 'owner_id'
Ran 8 tests - FAILED (errors=8)
```

A nested-payload case then proved that sensitive keys inside
`selected_option` were still retained before recursive minimization was added.

## GREEN evidence

```text
.venv/bin/python -m unittest \
  apps/referral-copilot/tests/test_auth.py \
  apps/referral-copilot/tests/test_persistence.py

Ran 14 tests - OK
```

The full Python suite subsequently passed with 93 tests. `npm test` passed four
tests, `npm audit --omit=dev --audit-level=high` reported zero vulnerabilities,
`pip check` reported no broken requirements, and Python compilation succeeded.

## Guarantees

| Guarantee | Evidence | Result |
|---|---|---|
| Deployed mode requires a valid proxy user and 32-byte secret pepper | `test_auth.py` | PASS |
| Raw user/email is not retained in the identity object | `test_databricks_identity_is_pseudonymous_and_stable` | PASS |
| Anonymous local mode cannot run with Databricks deployment markers | `test_local_demo_is_blocked_inside_a_databricks_app` | PASS |
| Every durable read/write/list/delete binds pseudonymous owner and plan ID | `test_persistence.py` owner-isolation cases | PASS |
| Same plan ID can safely exist for two owners | `test_owner_cannot_read_or_list_another_owners_records` | PASS |
| Sensitive intake and nested sensitive keys are discarded | `test_sensitive_intake_is_not_persisted_with_the_saved_decision` | PASS |
| Feedback statuses/notes and payload sizes are bounded | persistence validation cases | PASS |
| Deletion affects only the owner's plan and cascaded feedback | `test_owner_can_delete_own_plan_and_feedback_only` | PASS |

## Known live gaps

Unit tests do not prove Databricks OAuth routing, **CAN USE** permissions,
forwarded headers, Lakebase constraints, OAuth token rotation, scheduled expiry
purging, or UI wiring. Those require the two-user deployment test matrix in
`docs/security/login-and-persistence-audit.md`.

No coverage package is installed in the repository environment, so a numeric
coverage percentage was not fabricated. All newly added auth and persistence
public paths are exercised by the 14 targeted tests.
