#!/usr/bin/env python3
"""Bounded Tavily discovery into a separate review ledger.

Default mode is a dry run. ``--apply`` requires an explicit API key and still
creates only ``candidate`` rows; a human must verify each source/address before
the app may use it for routing.  No patient request is sent to Tavily.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
from src.address_enrichment import AddressEnrichment, read_ledger, utc_now, write_ledger  # noqa: E402
from src.web_evidence import search_public_sources  # noqa: E402

def rows(path: Path):
    content = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not isinstance(content, list): raise ValueError("Input must be a JSON or JSONL list of facility rows.")
    return [row for row in content if isinstance(row, dict) and str(row.get("unique_id") or row.get("facility_id") or "").strip()]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=APP_ROOT / "data" / "facility_address_candidates.jsonl")
    parser.add_argument("--max-records", type=int, default=25)
    parser.add_argument("--apply", action="store_true", help="Call Tavily; otherwise print planned work only.")
    args = parser.parse_args()
    if not 1 <= args.max_records <= 250: parser.error("--max-records must be 1..250 per run.")
    source_rows = rows(args.input)
    existing = read_ledger(args.output)
    pending = [row for row in source_rows if str(row.get("unique_id") or row.get("facility_id")) not in existing][:args.max_records]
    print(f"{len(pending)} facilities selected; {len(existing)} ledger rows already exist.")
    if not args.apply:
        print("Dry run only. Re-run with --apply after setting TAVILY_API_KEY and confirming your credit budget.")
        return 0
    if not (os.getenv("TAVILY_API_KEY") or "").strip() or (os.getenv("TAVILY_API_KEY") or "").upper().startswith("TODO"):
        parser.error("TAVILY_API_KEY is required for --apply.")
    for row in pending:
        facility_id = str(row.get("unique_id") or row.get("facility_id"))
        name = str(row.get("name") or row.get("facility_name") or "").strip()
        try:
            candidates = search_public_sources(name, "official address contact")
        except RuntimeError:
            continue
        if not candidates: continue
        source = candidates[0]
        existing[facility_id] = AddressEnrichment(facility_id=facility_id, facility_name=name, address_text=None, city=str(row.get("address_city") or "") or None, state=None, latitude=None, longitude=None, source_url=source.url, source_title=source.title, source_excerpt=source.snippet, retrieved_at=utc_now(), review_status="candidate")
    write_ledger(args.output, existing.values())
    print(f"Wrote {len(existing)} separate candidate rows to {args.output}. None are trusted for routing until reviewed.")
    return 0
if __name__ == "__main__": raise SystemExit(main())
