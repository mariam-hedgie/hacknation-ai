-- SUPERSEDED (see TODO.md "Decision — Model B adopted"): this describes Model A
-- (facilities_normalized / facility_claims_evidence / ...), which was never
-- built. The real table is workspace.default.facilities_searchable, built by
-- ../extract_data.py + ../flatten_data.py. Kept for reference only.
--
-- Data Legend phase 1: preserve the source and profile it before feature work.
-- Replace both identifiers once. Never paste patient data or secrets here.

CREATE SCHEMA IF NOT EXISTS <TARGET_CATALOG>.referral_copilot;

CREATE OR REPLACE TABLE <TARGET_CATALOG>.referral_copilot.facilities_raw AS
WITH hashed AS (
  SELECT
    *,
    sha2(to_json(struct(*)), 256) AS source_row_hash
  FROM <MARKETPLACE_CATALOG>.<SCHEMA>.<FACILITY_TABLE>
), numbered AS (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY source_row_hash
      ORDER BY source_row_hash
    ) AS duplicate_ordinal
  FROM hashed
)
SELECT
  *,
  concat(source_row_hash, '-', duplicate_ordinal) AS source_row_id,
  '<MARKETPLACE_CATALOG>.<SCHEMA>.<FACILITY_TABLE>' AS source_table,
  current_timestamp() AS ingested_at
FROM numbered;

-- Required gate: the brief says the supplied dataset contains 10,000 records.
SELECT
  count(*) AS row_count,
  count(DISTINCT source_row_id) AS unique_source_row_ids,
  count(*) - count(DISTINCT source_row_hash) AS duplicate_rows
FROM <TARGET_CATALOG>.referral_copilot.facilities_raw;

-- Inspect the live schema before configuring 02_build_evidence_tables.py.
DESCRIBE TABLE <TARGET_CATALOG>.referral_copilot.facilities_raw;

-- Inspect every column's null coverage without changing any raw value.
-- In a notebook, use the generated profiling query from the next command:
--   SELECT concat_ws(',\n', collect_list(...)) FROM ...
-- At minimum record coverage for the PDF's named concepts: description,
-- capability, procedure, equipment, source URL, numberDoctors, capacity, and
-- yearEstablished. Save aggregate results only; do not export source rows.
