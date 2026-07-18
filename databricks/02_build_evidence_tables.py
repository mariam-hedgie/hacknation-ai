# Databricks notebook source
"""Build normalized facility, literal evidence, and source-chunk tables.

Set the widgets to the live table and its real columns after running phase 1.
No model-generated text is accepted as evidence: every stored cited span is
verified as a literal substring of its source value.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pyspark.sql import functions as F, types as T


dbutils.widgets.text("source_table", "<TARGET_CATALOG>.referral_copilot.facilities_raw")
dbutils.widgets.text("target_schema", "<TARGET_CATALOG>.referral_copilot")
dbutils.widgets.text(
    "column_mapping_json",
    json.dumps(
        {
            "facility_id": "facilityId",
            "display_name": "facilityName",
            "location": "address",
            "latitude": "latitude",
            "longitude": "longitude",
            "facility_type": "facilityType",
            "source_url": "sourceUrl",
            "claim_fields": ["capability", "procedures", "equipment"],
            "chunk_fields": ["description", "capability", "procedures", "equipment"],
        }
    ),
)


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){1,2}$")


def checked_identifier(value: str, label: str) -> str:
    value = value.strip()
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a two- or three-part Databricks identifier")
    return value


def text_items(value: Any) -> list[str]:
    """Return conservative literal items from list-like source values."""

    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    elif isinstance(value, dict):
        raw_items = list(value.values())
    else:
        raw = str(value).strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, list):
            raw_items = parsed
        else:
            # Avoid comma splitting: commas often belong inside procedure names.
            raw_items = re.split(r"[;|\n]+", raw)
    cleaned: list[str] = []
    for item in raw_items:
        text = str(item).strip().strip("[]\"'")
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


source_table = checked_identifier(dbutils.widgets.get("source_table"), "source_table")
target_schema = checked_identifier(dbutils.widgets.get("target_schema"), "target_schema")
mapping = json.loads(dbutils.widgets.get("column_mapping_json"))
raw = spark.table(source_table)
available = set(raw.columns)

required_mapping = {"display_name", "claim_fields", "chunk_fields"}
missing_mapping = required_mapping - set(mapping)
if missing_mapping:
    raise ValueError(f"Missing mapping keys: {sorted(missing_mapping)}")
if not isinstance(mapping["claim_fields"], list) or not mapping["claim_fields"]:
    raise ValueError("claim_fields must contain at least one mapped source field")
if not isinstance(mapping["chunk_fields"], list) or not mapping["chunk_fields"]:
    raise ValueError("chunk_fields must contain at least one mapped source field")

mapped_columns = {
    value
    for key, value in mapping.items()
    if key not in {"claim_fields", "chunk_fields"} and isinstance(value, str)
}
mapped_columns.update(mapping["claim_fields"])
mapped_columns.update(mapping["chunk_fields"])
missing_columns = sorted(mapped_columns - available)
if missing_columns:
    raise ValueError(
        "Column mapping does not match the live table. Profile and correct: "
        + ", ".join(missing_columns)
    )

profile_columns = sorted(mapped_columns)
raw.select(
    F.count(F.lit(1)).alias("row_count"),
    *[
        F.round(
            100
            * F.avg(
                F.when(
                    F.col(column).isNotNull()
                    & (F.length(F.trim(F.col(column).cast("string"))) > 0),
                    1,
                ).otherwise(0)
            ),
            1,
        ).alias(f"{column}_coverage_pct")
        for column in profile_columns
    ],
).show(truncate=False)


def mapped(name: str, cast: str = "string"):
    source = mapping.get(name)
    return F.col(source).cast(cast) if source else F.lit(None).cast(cast)


normalised = raw.select(
    F.coalesce(
        mapped("facility_id"),
        F.col("source_row_id").cast("string"),
    ).alias("facility_id"),
    mapped("display_name").alias("display_name"),
    mapped("location").alias("location"),
    mapped("latitude", "double").alias("lat"),
    mapped("longitude", "double").alias("lon"),
    mapped("facility_type").alias("facility_type"),
    mapped("source_url").alias("source_url"),
    F.col("source_row_id").cast("string").alias("source_row_id"),
)
normalised.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{target_schema}.facilities_normalized"
)

chunk_frames = []
for field in mapping["chunk_fields"]:
    chunk_frames.append(
        raw.select(
            F.col("source_row_id").cast("string").alias("source_row_id"),
            F.lit(field).alias("source_column"),
            F.col(field).cast("string").alias("literal_source_text"),
        ).where(F.col(field).isNotNull())
    )
chunks = chunk_frames[0]
for frame in chunk_frames[1:]:
    chunks = chunks.unionByName(frame)
chunks = chunks.where(F.length(F.trim("literal_source_text")) > 0).withColumn(
    "chunk_id",
    F.sha2(F.concat_ws("|", "source_row_id", "source_column"), 256),
).select("chunk_id", "source_row_id", "source_column", "literal_source_text")
chunks.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{target_schema}.facility_source_chunks"
)
spark.sql(
    f"ALTER TABLE {target_schema}.facility_source_chunks "
    "SET TBLPROPERTIES (delta.enableChangeDataFeed = true)"
)

to_items = F.udf(text_items, T.ArrayType(T.StringType(), containsNull=False))
claim_frames = []
for field in mapping["claim_fields"]:
    claim_frames.append(
        raw.select(
            F.col("source_row_id").cast("string").alias("source_row_id"),
            F.coalesce(mapped("facility_id"), F.col("source_row_id").cast("string")).alias(
                "facility_id"
            ),
            F.lit(field).alias("source_column"),
            F.col(field).cast("string").alias("literal_source_text"),
            F.explode(to_items(F.col(field))).alias("cited_span"),
        )
    )
evidence = claim_frames[0]
for frame in claim_frames[1:]:
    evidence = evidence.unionByName(frame)
evidence = (
    evidence.where(
        F.expr("instr(lower(literal_source_text), lower(cited_span))") > 0
    )
    .withColumn("capability", F.lower(F.trim("cited_span")))
    .withColumn(
        "evidence_id",
        F.sha2(
            F.concat_ws("|", "source_row_id", "source_column", "capability"),
            256,
        ),
    )
    .withColumn(
        "span_start",
        F.expr("instr(lower(literal_source_text), lower(cited_span))") - 1,
    )
    .withColumn("span_end", F.col("span_start") + F.length("cited_span"))
    .withColumn("extraction_method", F.lit("deterministic_literal_item_v1"))
    .select(
        "evidence_id",
        "facility_id",
        "capability",
        "source_column",
        "literal_source_text",
        "cited_span",
        "span_start",
        "span_end",
        "extraction_method",
        "source_row_id",
    )
    .dropDuplicates(["evidence_id"])
)
evidence.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{target_schema}.facility_claims_evidence"
)

# COMMAND ----------
# Required gates: zero broken literal receipts and no missing row identifiers.
spark.sql(
    f"""
    SELECT
      count(*) AS evidence_rows,
      count_if(instr(lower(literal_source_text), lower(cited_span)) = 0) AS broken_receipts,
      count_if(source_row_id IS NULL OR trim(source_row_id) = '') AS missing_row_ids,
      count(DISTINCT source_column) AS represented_source_fields
    FROM {target_schema}.facility_claims_evidence
    """
).show(truncate=False)
