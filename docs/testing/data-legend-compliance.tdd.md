# Data Legend compliance additions: TDD record

## Scope

This change adds only backend/data/compliance contracts. It intentionally does
not edit `apps/referral-copilot/app.py` or `docs/ui-handoff.md`, because the UI
owner's work has merge priority.

## Red

The trust and persistence tests were written before their modules. The first
run failed with:

```text
ModuleNotFoundError: No module named 'src.trust'
ModuleNotFoundError: No module named 'src.persistence'
```

Nearby-facility query tests were then written first and failed with:

```text
AttributeError: 'DatabricksFacilityRepository' object has no attribute
'find_by_capability_near'
```

## Green

Implemented and tested:

- literal-span receipts and distinct-field corroboration;
- ordinal weak/supported/strong/conflicting trust states;
- conflict precedence and explicit missing fields;
- Lakebase/Postgres upsert/reopen and append-only feedback contract;
- strict table-identifier validation and bound user values;
- coordinate validation and straight-line distance ordering in a parameterized
  Databricks query.

Final repository checks:

```text
85 Python tests passed
4 Node tests passed
compileall passed for apps/referral-copilot and databricks
Streamlit started on localhost and /_stcore/health returned ok
```

The Streamlit tests require the repository `.venv`; system Python lacks
Streamlit and is not the authoritative test environment.

## Not validated locally

Local tests cannot prove Databricks Free Edition feature access, challenge-data
schema/quality, AI Search index creation, Lakebase OAuth/resource wiring, app
service-principal permissions, or a live deployment URL. Those are explicit
manual gates in `docs/compliance/final-submission-gate.md`.
