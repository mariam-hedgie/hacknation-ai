from databricks import sql
import os
from dotenv import load_dotenv
import logging

import pandas as pd

logging.getLogger("databricks.sql").setLevel(logging.WARNING)
load_dotenv()

connection = sql.connect(
    server_hostname=os.getenv("SERVER_HOSTNAME"),
    http_path=os.getenv("HTTP_PATH"),
    access_token=os.getenv("ACCESS_TOKEN")
)
cursor = connection.cursor()

catalog = "workspace"
schema = "default"
table = f"{catalog}.{schema}.facilities_consolidated"

output_table = f"{catalog}.{schema}.facilities_searchable"
parsed = f"{catalog}.{schema}.facilities_parsed"
cleaned = f"{catalog}.{schema}.facilities_cleaned"
source_table = "databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities"

query = f"""
CREATE OR REPLACE TABLE {cleaned} AS
SELECT
    unique_id,
    name,
    regexp_replace(
        regexp_replace(
            consolidated_json,
            '^```json\\s*',
            ''
        ),
        '\\s*```$',
        ''
    ) AS clean_json
FROM {table};
"""

cursor.execute(query)

query = f"""
CREATE OR REPLACE TABLE {parsed} AS
SELECT
    unique_id,
    name,
    from_json(
        clean_json,
        '''
        STRUCT<
            capabilities: ARRAY<STRUCT<
                claim: STRING,
                evidence: ARRAY<STRING>
            >>,
            procedures: ARRAY<STRUCT<
                claim: STRING,
                evidence: ARRAY<STRING>
            >>,
            equipment: ARRAY<STRUCT<
                claim: STRING,
                evidence: ARRAY<STRING>
            >>,
            specialties: ARRAY<STRING>,
            facility_facts: ARRAY<STRUCT<
                fact: STRING,
                evidence: ARRAY<STRING>
            >>,
            data_quality: STRUCT<
                has_rich_description: BOOLEAN,
                conflicting_claims: ARRAY<STRING>,
                possible_merged_facility: BOOLEAN,
                merge_suspicion_reason: STRING
            >
        >
        '''
    ) AS data

FROM {cleaned};
"""

cursor.execute(query)

query = f"""
CREATE OR REPLACE TABLE {output_table} AS
SELECT
    parsed.unique_id,
    parsed.name,

    parsed.data.specialties,

    parsed.data.capabilities,

    parsed.data.procedures,

    parsed.data.equipment,

    parsed.data.facility_facts,

    parsed.data.data_quality,

    concat_ws(
      ' ',
      coalesce(parsed.name, ''),
      coalesce(to_json(parsed.data.specialties), ''),
      coalesce(to_json(parsed.data.capabilities), ''),
      coalesce(to_json(parsed.data.procedures), ''),
      coalesce(to_json(parsed.data.equipment), ''),
      coalesce(to_json(parsed.data.facility_facts), '')
    ) AS search_text,

    -- Preserve the original row fields so the app can revalidate every
    -- machine-extracted evidence span before displaying it as documented.
    source.description AS raw_description,
    source.capability AS raw_capability,
    source.procedure AS raw_procedure,
    source.equipment AS raw_equipment,

    TRY_CAST(source.latitude AS DOUBLE) AS latitude,
    TRY_CAST(source.longitude AS DOUBLE) AS longitude,
    source.address_city,
    source.facilityTypeId AS facility_type,
    CASE
      WHEN lower(trim(source.operatorTypeId)) IN ('public', 'private', 'government')
        THEN lower(trim(source.operatorTypeId))
      ELSE NULL
    END AS operator_type

FROM {parsed} AS parsed
LEFT JOIN {source_table} AS source
  ON CAST(source.unique_id AS STRING) = CAST(parsed.unique_id AS STRING);
"""

cursor.execute(query)

cursor.close()
connection.close()
