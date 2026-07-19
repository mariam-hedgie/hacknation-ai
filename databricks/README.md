# Databricks evidence and persistence setup

The challenge dataset stays in Databricks and must never be committed here.
Use the complete teammate checklist in
[`../docs/databricks-team-handoff.md`](../docs/databricks-team-handoff.md).

## Active application path

The deployed React app currently queries:

```text
official facilities table
  -> ../extract_data.py
  -> workspace.default.facilities_consolidated
  -> ../flatten_data.py
  -> workspace.default.facilities_searchable
  -> AI Search
  -> literal raw-field validator
  -> explainable shortlist
```

Run `05_vector_search_setup.md` after rebuilding the corrected searchable table.
Run `lakebase_schema.sql` only in the Lakebase SQL editor.

The numbered `01`–`04` files preserve the alternative normalized evidence-table
design and its audit queries. They are useful reference/evaluation material but
are not the table shape queried by the current `src/backend/vector_search.py`.
Do not run both architectures and assume the app reads whichever completed.

## Non-negotiable gates

- Preserve original raw source fields and `unique_id` in every searchable row.
- Accept a displayed claim only when its cited span occurs literally in the
  preserved raw field.
- Treat absent/invalid data as unknown, never unavailable or zero.
- Validate coordinates and operator type; do not repair misaligned source rows
  by guessing.
- Use the App service principal and attached resources, never a committed PAT.
- Persist only minimized user decisions in owner-scoped Lakebase tables.
- Complete every live proof item in
  [`../docs/compliance/final-submission-gate.md`](../docs/compliance/final-submission-gate.md).

Local code or a seeded card is not proof of the official 10,000-row dataset,
live AI Search, or cross-session Lakebase persistence.
