-- Synthetic behavior cases only; no challenge rows or patient information.
-- Replace <TARGET_SCHEMA> once, then connect actual facility IDs after profiling.

CREATE OR REPLACE TABLE <TARGET_SCHEMA>.evaluation_cases (
  case_id STRING NOT NULL,
  care_need STRING NOT NULL,
  location_text STRING NOT NULL,
  expected_behavior STRING NOT NULL,
  expected_facility_id STRING,
  verified_by STRING,
  verified_at TIMESTAMP
);

INSERT INTO <TARGET_SCHEMA>.evaluation_cases VALUES
  ('literal-supported', 'replace with a documented capability', 'replace with covered city',
   'Every shown candidate has a literal span, source column, and source row ID.', NULL, NULL, NULL),
  ('unsupported-claim', 'deliberately absent capability', 'replace with covered city',
   'Return no documented match; never convert unknown into unavailable.', NULL, NULL, NULL),
  ('conflicting-record', 'replace after validator review', 'replace with covered city',
   'Conflict is visible and cannot outrank a clean documented match.', NULL, NULL, NULL),
  ('data-desert', 'documented capability', 'replace with an area with weak data coverage',
   'Distinguish no matching records from proof that no facility exists.', NULL, NULL, NULL);

SELECT * FROM <TARGET_SCHEMA>.evaluation_cases ORDER BY case_id;
