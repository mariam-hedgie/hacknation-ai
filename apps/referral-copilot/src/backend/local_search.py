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

def _default_data_path() -> Path:
    """Locate the optional local facility extract.

    Searches upward for `data/facilities_searchable.json` instead of indexing a
    fixed ancestor: a deployed copy of src/ need not sit at the repository's
    directory depth (a container image roots it at /app). Falls back to the
    repository-relative location, which simply will not exist when absent —
    this retriever is optional and reports itself unavailable.
    """

    here = Path(__file__).resolve()
    for candidate in here.parents:
        extract = candidate / "data" / "facilities_searchable.json"
        if extract.is_file():
            return extract
    return here.parents[min(4, len(here.parents) - 1)] / "data" / "facilities_searchable.json"


_DEFAULT_DATA_PATH = _default_data_path()

_MATCH_GROUPS = ("capabilities", "procedures", "equipment")


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


class LocalDataRetriever:
    def __init__(self, data_path: str | os.PathLike[str] | None = None) -> None:
        self._data_path = Path(data_path) if data_path is not None else self._resolve_path()
        self._rows: list[dict[str, Any]] | None = None
        self._load_attempted = False

    @staticmethod
    def _resolve_path() -> Path:
        override = os.environ.get("AVEN_LOCAL_DATA_PATH", "").strip()
        return Path(override) if override else _DEFAULT_DATA_PATH

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
                data = json.load(f)
            self._rows = data if isinstance(data, list) else None
        except Exception:
            self._rows = None
        return self._rows

    def retrieve(self, capability: str, location: str | None, *, k: int = 20) -> list[dict[str, Any]] | None:
        """Return up to `k` candidate rows matching `capability`, or None if
        the local snapshot is unavailable/unreadable.

        `location` is accepted for interface parity with vector_search.retrieve
        but not used to filter: this dataset carries no coordinates (see
        agent_bricks.py's distance_km=None note), so pretending to filter by
        distance here would fabricate precision the data doesn't support.
        """
        rows = self._load()
        if rows is None:
            return None
        needed = _normalise(capability)
        if not needed:
            return []
        matches = [row for row in rows if _row_matches(row, needed)]
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
