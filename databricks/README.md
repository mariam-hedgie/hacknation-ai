# Databricks evidence pipeline

These files implement the repository side of the Data Legend data contract. The
challenge dataset itself stays in Databricks and must never be committed here.

Run in this order in the **same Databricks Free Edition workspace** that hosts
the final app:

1. Subscribe to the organizer-linked Marketplace dataset from page 4 of the
   original brief.
2. Run `01_ingest_and_profile.sql`; replace the two angle-bracket identifiers
   once, after inspecting the source schema.
3. In `02_build_evidence_tables.py`, set the source table, target schema, and
   actual column mapping in the notebook widgets. Run every cell.
4. Run `03_build_trust_assessment.sql` after replacing `<TARGET_SCHEMA>`.
5. Run `04_seed_evaluation_cases.sql` after replacing `<TARGET_SCHEMA>`.
6. Complete the index gate in `05_vector_search_setup.md`.
7. Run `lakebase_schema.sql` in the Lakebase SQL editor, not the lakehouse SQL
   editor.

Do not call the pipeline complete until the output checks at the bottom of each
file pass on the provided 10,000-record dataset. A code file in GitHub is not
proof that its corresponding Databricks table exists.

The mapping step is intentionally explicit. The PDF names concepts and example
coverage but the live subscribed table is authoritative for exact column names
and types. If a requested fact is absent, preserve it as `not documented`; do
not manufacture a replacement.
