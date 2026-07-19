"""Separate, review-gated facility address enrichment ledger.

This module never mutates the challenge facility snapshot.  Web-discovered
addresses are candidates until a reviewer verifies a first-party or official
source.  Only ``verified`` rows may be merged into local retrieval for routing.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

VALID_REVIEW_STATES = {"candidate", "verified", "rejected", "needs_review"}


@dataclass(frozen=True)
class AddressEnrichment:
    facility_id: str
    facility_name: str
    address_text: str | None
    city: str | None
    state: str | None
    latitude: float | None
    longitude: float | None
    source_url: str
    source_title: str
    source_excerpt: str
    retrieved_at: str
    review_status: str = "candidate"
    reviewed_at: str | None = None
    reviewer: str | None = None

    def __post_init__(self) -> None:
        if not self.facility_id.strip() or not self.facility_name.strip():
            raise ValueError("Address enrichment requires a stable facility ID and name.")
        if self.review_status not in VALID_REVIEW_STATES:
            raise ValueError("Invalid address-enrichment review status.")
        if not self.source_url.startswith(("https://", "http://")):
            raise ValueError("Address enrichment requires an http(s) source URL.")
        if self.review_status == "verified" and not self.address_text:
            raise ValueError("A verified address requires address text.")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_ledger(path: str | Path) -> dict[str, AddressEnrichment]:
    ledger: dict[str, AddressEnrichment] = {}
    candidate_path = Path(path)
    if not candidate_path.is_file():
        return ledger
    for line in candidate_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = AddressEnrichment(**json.loads(line))
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        ledger[record.facility_id] = record
    return ledger


def write_ledger(path: str | Path, rows: Iterable[AddressEnrichment]) -> None:
    """Atomically replace only the separate ledger after validation."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda item: item.facility_id)
    payload = "".join(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in ordered)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(destination)


def verified_locations(path: str | Path) -> Mapping[str, AddressEnrichment]:
    return {key: row for key, row in read_ledger(path).items() if row.review_status == "verified"}
