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
    unique_id,
    name,

    data.specialties,

    data.capabilities,

    data.procedures,

    data.equipment,

    data.facility_facts,

    data.data_quality

FROM {parsed};
"""

cursor.execute(query)

cursor.close()
connection.close()
