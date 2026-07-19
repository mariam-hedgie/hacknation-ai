"""Pull `facilities_searchable` down to a local JSON file.

Read-only counterpart to extract_data.py / flatten_data.py: those two build
and repeatedly overwrite the Databricks tables (extract_data.py's ai_query
step costs real serving credit across ~10k rows; flatten_data.py's
CREATE OR REPLACE TABLE mutates them) — this script does neither. It just
SELECTs the already-built, already-flattened table and writes it to disk, so
the rest of the project (or a human) can work from a local snapshot without a
live Databricks connection.

Requires the same SERVER_HOSTNAME / HTTP_PATH / ACCESS_TOKEN as
extract_data.py / flatten_data.py / database.py in this repo (a personal
access token via .env, not the app's DATABRICKS_* service-identity config —
see apps/referral-copilot/src/backend/config.py for why those are kept
separate). Never commit the output file or a token.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from databricks import sql
from dotenv import load_dotenv

load_dotenv()

CATALOG = "workspace"
SCHEMA = "default"
TABLE = f"{CATALOG}.{SCHEMA}.facilities_searchable"

OUTPUT_PATH = Path("data/facilities_searchable.json")


def _to_jsonable(value):
    """Recursively convert whatever the connector hands back for ARRAY/STRUCT
    columns (dicts, lists, or Row-like objects, depending on connector
    version) into plain JSON-serializable Python values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    as_dict = getattr(value, "asDict", None)
    if callable(as_dict):
        return _to_jsonable(as_dict())
    return str(value)


def download(output_path: Path = OUTPUT_PATH) -> int:
    """Fetch every row of `facilities_searchable` and write it as a local
    JSON array. Returns the row count written."""
    connection = sql.connect(
        server_hostname=os.getenv("SERVER_HOSTNAME"),
        http_path=os.getenv("HTTP_PATH"),
        access_token=os.getenv("ACCESS_TOKEN"),
    )
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {TABLE}")
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
    finally:
        connection.close()

    records = [_to_jsonable(row) for row in rows]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(records)


if __name__ == "__main__":
    print(f"Downloading {TABLE} to {OUTPUT_PATH} ...")
    start = time.time()
    count = download()
    print(f"Wrote {count} rows to {OUTPUT_PATH} in {time.time() - start:.1f}s.")
