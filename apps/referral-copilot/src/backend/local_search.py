"""Local-file retrieval seam — real facility data with no live Databricks
connection required.

Drop-in alternate source for the same seam vector_search.py fills: returns raw
candidate rows in the exact `facilities_searchable` (Model B) shape
`agent_bricks.assess_claims` / `enrichment.normalize` already expect. Used as
a fallback when live Vector Search isn't configured but a local snapshot
exists on disk (see download_facilities.py) — e.g. a demo environment with no
Databricks credentials. Returns None on any failure, exactly like every other
seam here, so a missing/corrupt file never breaks the app.

This is real, source-grounded facility data — not seeded/fabricated demo
content — but it is a static local snapshot, not a live connection. Callers
must label it accordingly (see service.status()["local_data"]) rather than
claiming it as a live Databricks result.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..address_enrichment import verified_locations

def _default_data_path() -> Path:
    """Locate the optional local facility extract.

    Searches upward for either supported export format. A deployed copy of src/
    need not sit at the repository's directory depth, so this also works in a
    container image rooted at /app.
    """

    here = Path(__file__).resolve()
    for candidate in here.parents:
        for filename in ("facilities_searchable.json", "facilities_searchable.jsonl"):
            extract = candidate / "data" / filename
            if extract.is_file():
                return extract
    return here.parents[min(4, len(here.parents) - 1)] / "data" / "facilities_searchable.json"


_DEFAULT_DATA_PATH = _default_data_path()
_DEFAULT_ENRICHMENT_PATH = _DEFAULT_DATA_PATH.parent / "facility_address_candidates.jsonl"

_MATCH_GROUPS = ("capabilities", "procedures", "equipment")
_LOCATION_ALIASES = {
    "bengaluru": ("bengaluru", "bangalore"),
    "delhi": ("delhi", "new delhi"),
    "jaipur": ("jaipur",),
    "mumbai": ("mumbai", "bombay", "navi mumbai"),
    "patna": ("patna",),
    "pune": ("pune",),
}
_SERIALIZED_COLUMNS = (
    "specialties",
    "capabilities",
    "procedures",
    "equipment",
    "facility_facts",
    "data_quality",
)


def _normalise(text: str) -> str:
    return " ".join((text or "").casefold().split())


def _row_matches(row: dict[str, Any], needed: str) -> bool:
    """Tolerant substring match against claim text and specialty tags — the
    same approach agent_bricks._find_matching_entry uses downstream, kept
    consistent so a row that matches here is likely to match there too."""
    for group in _MATCH_GROUPS:
        for entry in row.get(group) or []:
            claim = _normalise(entry.get("claim", "") if isinstance(entry, dict) else "")
            if claim and (needed in claim or claim in needed):
                return True
    for specialty in row.get("specialties") or []:
        if needed in _normalise(str(specialty)):
            return True
    return False


def _known_city_aliases(location: str | None) -> tuple[str, ...]:
    normalized = _normalise(location or "")
    for aliases in _LOCATION_ALIASES.values():
        if any(alias in normalized for alias in aliases):
            return aliases
    return ()


def _row_mentions_city(row: dict[str, Any], aliases: tuple[str, ...]) -> bool:
    """Use only an explicit city mention when local rows lack coordinates."""
    if not aliases:
        return True
    text = _normalise(
        " ".join(
            str(row.get(key) or "")
            for key in ("name", "address_city", "facility_facts")
        )
    )
    return any(alias in text for alias in aliases)


def _decode_row(row: Any) -> dict[str, Any] | None:
    """Decode JSON-serialized complex columns from Databricks JSONL exports."""
    if not isinstance(row, dict):
        return None
    decoded = dict(row)
    for column in _SERIALIZED_COLUMNS:
        value = decoded.get(column)
        if not isinstance(value, str):
            continue
        try:
            decoded[column] = json.loads(value)
        except json.JSONDecodeError:
            # Preserve the value so the downstream normalizer can fail closed.
            pass
    return decoded


class LocalDataRetriever:
    def __init__(self, data_path: str | os.PathLike[str] | None = None) -> None:
        self._data_path = Path(data_path) if data_path is not None else self._resolve_path()
        self._rows: list[dict[str, Any]] | None = None
        self._load_attempted = False

    @staticmethod
    def _resolve_path() -> Path:
        override = os.environ.get("AVEN_LOCAL_DATA_PATH", "").strip()
        if override:
            return Path(override)
        return _DEFAULT_DATA_PATH

    def available(self) -> bool:
        return self._data_path.is_file()

    def _load(self) -> list[dict[str, Any]] | None:
        if self._rows is not None:
            return self._rows
        if self._load_attempted:
            return None
        self._load_attempted = True
        try:
            with open(self._data_path, encoding="utf-8") as f:
                if self._data_path.suffix.casefold() == ".jsonl":
                    data = [json.loads(line) for line in f if line.strip()]
                else:
                    data = json.load(f)
            if not isinstance(data, list):
                self._rows = None
            else:
                decoded_rows = [row for row in (_decode_row(row) for row in data) if row is not None]
                # Only reviewer-approved branch locations are attached. Candidate
                # web discoveries remain isolated and cannot affect a route.
                approved = verified_locations(_DEFAULT_ENRICHMENT_PATH)
                for row in decoded_rows:
                    facility_id = str(row.get("unique_id") or row.get("facility_id") or "")
                    enrichment = approved.get(facility_id)
                    if enrichment is None:
                        continue
                    row["address_city"] = enrichment.city or row.get("address_city")
                    row["address_text"] = enrichment.address_text
                    row["latitude"] = enrichment.latitude
                    row["longitude"] = enrichment.longitude
                    row["address_source_url"] = enrichment.source_url
                self._rows = decoded_rows
        except Exception:
            self._rows = None
        return self._rows

    def retrieve(self, capability: str, location: str | None, *, k: int = 20) -> list[dict[str, Any]] | None:
        """Return up to `k` candidate rows matching `capability`, or None if
        the local snapshot is unavailable/unreadable.

        When the entered location names a supported city, rows must explicitly
        mention that city. The snapshot lacks coordinates, so Aven still shows
        the distance as unknown instead of pretending it enforced an exact
        kilometre radius.
        """
        rows = self._load()
        if rows is None:
            return None
        needed = _normalise(capability)
        if not needed:
            return []
        city_aliases = _known_city_aliases(location)
        matches = [
            row
            for row in rows
            if _row_matches(row, needed) and _row_mentions_city(row, city_aliases)
        ]
        return matches[:k]

    def count_matches(self, capability: str, *, sample_size: int = 20) -> tuple[int, list[dict[str, Any]]] | None:
        """Full-dataset match count plus a capped sample, for aggregate
        questions ("how many facilities document X?") where `retrieve`'s
        k-cap would silently undercount. Returns None on the same conditions
        `retrieve` does (unavailable/unreadable snapshot)."""
        rows = self._load()
        if rows is None:
            return None
        needed = _normalise(capability)
        if not needed:
            return 0, []
        matches = [row for row in rows if _row_matches(row, needed)]
        return len(matches), matches[:sample_size]
