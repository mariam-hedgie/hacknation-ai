-- Data Legend phase 3: ordinal trust, gaps, and reviewer-confirmed conflicts.
-- Replace <TARGET_SCHEMA> once. No probability or clinical-quality score is used.

CREATE TABLE IF NOT EXISTS <TARGET_SCHEMA>.facility_claim_conflicts (
  facility_id STRING NOT NULL,
  capability STRING NOT NULL,
  contradiction_note STRING NOT NULL,
  validator STRING,
  validated_at TIMESTAMP
);

CREATE OR REPLACE TABLE <TARGET_SCHEMA>.facility_trust_assessment AS
WITH corroboration AS (
  SELECT
    facility_id,
    capability,
    count(DISTINCT source_column) AS corroboration_count,
    collect_set(source_column) AS corroborating_fields
  FROM <TARGET_SCHEMA>.facility_claims_evidence
  GROUP BY facility_id, capability
), gaps AS (
  SELECT
    facility_id,
    filter(
      array(
        IF(max(IF(location IS NOT NULL AND trim(location) <> '', 1, 0)) = 0, 'location', NULL),
        IF(max(IF(lat IS NOT NULL AND lon IS NOT NULL, 1, 0)) = 0, 'coordinates', NULL),
        IF(max(IF(facility_type IS NOT NULL AND trim(facility_type) <> '', 1, 0)) = 0, 'facility_type', NULL),
        IF(max(IF(source_url IS NOT NULL AND trim(source_url) <> '', 1, 0)) = 0, 'source_url', NULL)
      ),
      item -> item IS NOT NULL
    ) AS missing_fields
  FROM <TARGET_SCHEMA>.facilities_normalized
  GROUP BY facility_id
), conflicts AS (
  SELECT
    facility_id,
    capability,
    true AS contradiction_flag,
    concat_ws(' | ', collect_set(contradiction_note)) AS contradiction_notes
  FROM <TARGET_SCHEMA>.facility_claim_conflicts
  GROUP BY facility_id, capability
)
SELECT
  c.facility_id,
  c.capability,
  c.corroboration_count,
  coalesce(x.contradiction_flag, false) AS contradiction_flag,
  coalesce(g.missing_fields, CAST(array() AS ARRAY<STRING>)) AS missing_fields,
  CASE
    WHEN coalesce(x.contradiction_flag, false) THEN 'conflicting'
    WHEN c.corroboration_count >= 3 THEN 'documented'
    WHEN c.corroboration_count >= 1 THEN 'documented'
    ELSE 'not_documented'
  END AS data_status,
  CASE
    WHEN coalesce(x.contradiction_flag, false)
      THEN concat('Conflicting source information: ', x.contradiction_notes)
    WHEN c.corroboration_count >= 3
      THEN 'Literal evidence is corroborated across at least three distinct source fields.'
    WHEN c.corroboration_count = 2
      THEN 'Literal evidence is corroborated across two distinct source fields.'
    ELSE 'Literal evidence appears in one source field and should be double-checked.'
  END AS explanation
FROM corroboration c
LEFT JOIN gaps g USING (facility_id)
LEFT JOIN conflicts x USING (facility_id, capability);

-- Required review: inspect weak, incomplete, and conflicting claims before demo.
SELECT *
FROM <TARGET_SCHEMA>.facility_trust_assessment
WHERE corroboration_count = 1
   OR size(missing_fields) > 0
   OR contradiction_flag
ORDER BY contradiction_flag DESC, size(missing_fields) DESC;
