"""Agent Bricks seam — extraction, trust scoring, and self-correction.

Turns noisy retrieved rows into source-grounded `FacilityCandidate` objects with
an honest `EvidenceStatus`. This is where the brief's "Trust Scorer" lives: a
claim with no corroborating text must not read the same as one backed across
fields, and a data desert must be distinguishable from a medical desert.

The extraction itself already happened upstream (see TODO.md's "Agent Bricks
is much smaller than the old TODO claimed" finding): rows arrive from
`vector_search.retrieve()` in the `facilities_searchable` (Model B) shape —
`enrichment.normalize()`'s documented extractor output schema, one row per
facility. `assess_claims` is therefore a pure mapper, not an LLM call:

    row -> enrichment.normalize(row)
        -> pick the claim group entry matching the requested capability
        -> domain.evidence_status(span, has_conflict=...)
        -> FacilityCandidate(facility_id=unique_id, display_name=name, ...)
        -> missing_fields for every claim group that came back empty

Returns None when unavailable so the service falls back to seeded demo options.

The mapper re-verifies every extracted span against the preserved original
dataset field. A span without that row/column receipt fails closed as
``not_documented`` and cannot enter the shortlist as a confirmed match.
"""

from __future__ import annotations

import math
from typing import Any

from .. import enrichment
from ..domain import EvidenceStatus, FacilityCandidate, evidence_status
from .config import BackendConfig

# Claim groups searched for a match to the requested capability, in priority
# order. `facility_facts` is excluded: it describes the facility generally
# (accessibility, hours) rather than a service/procedure/equipment claim, so it
# is never a match target — only a `missing_fields` / display concern.
_CAPABILITY_GROUPS: tuple[str, ...] = ("capabilities", "procedures", "equipment")


def _normalise(text: str) -> str:
    return " ".join((text or "").casefold().split())


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _find_matching_entry(
    normalized: dict[str, Any], capability: str
) -> tuple[str, dict[str, Any]] | None:
    """Return (group_key, entry) for the first claim matching `capability`.

    Matching is substring-tolerant in either direction: retrieval already
    matched semantically on this capability, but the extractor's claim text
    and the user's/task's capability string are free text and rarely identical
    ("cardiology" vs "outpatient cardiology consultation").
    """
    needed = _normalise(capability)
    if not needed:
        return None
    for key in _CAPABILITY_GROUPS:
        for entry in normalized.get(key, []):
            claim_text = _normalise(entry.get("claim", ""))
            if claim_text and (needed in claim_text or claim_text in needed):
                return key, entry
    return None


_RAW_FIELDS = {
    "capabilities": ("raw_capability",),
    "procedures": ("raw_procedure",),
    "equipment": ("raw_equipment",),
    "facility_facts": ("raw_description", "raw_capability", "raw_procedure"),
}

_CITY_CENTRES = {
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "delhi": (28.6139, 77.2090),
    "jaipur": (26.9124, 75.7873),
    "mumbai": (19.0760, 72.8777),
    "patna": (25.5941, 85.1376),
    "pune": (18.5204, 73.8567),
}


def _verified_receipts(
    row: dict[str, Any], group_key: str, entry: dict[str, Any]
) -> tuple[tuple[str, str, str], ...]:
    """Return only spans found literally in the original dataset field."""

    receipts: list[tuple[str, str, str]] = []
    for span in entry.get("evidence", []):
        for raw_field in _RAW_FIELDS.get(group_key, ()):
            source_text = _text(row.get(raw_field))
            if source_text and _normalise(span) in _normalise(source_text):
                receipts.append((raw_field, source_text, _text(span)))
                break
    return tuple(receipts)


def _coordinate(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _origin_coordinates(location: str | None) -> tuple[float, float] | None:
    normalized = _normalise(location or "")
    for city, coordinates in _CITY_CENTRES.items():
        if city in normalized:
            return coordinates
    return None


def _straight_line_distance_km(
    location: str | None, row: dict[str, Any]
) -> float | None:
    origin = _origin_coordinates(location)
    latitude = _coordinate(row.get("latitude"))
    longitude = _coordinate(row.get("longitude"))
    if origin is None or latitude is None or longitude is None:
        return None
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None
    lat1, lon1 = map(math.radians, origin)
    lat2, lon2 = math.radians(latitude), math.radians(longitude)
    delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return round(6371.0 * 2 * math.asin(math.sqrt(haversine)), 1)


def _facility_type(row: dict[str, Any]) -> str | None:
    operator = _normalise(_text(row.get("operator_type")))
    if operator in {"public", "private"}:
        return operator
    if operator == "government":
        return "public"
    return None


def _missing_claim_groups(normalized: dict[str, Any]) -> tuple[str, ...]:
    return tuple(key for key, _, _ in enrichment.CLAIM_GROUPS if not normalized.get(key))


class AgentBricksClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        # No self._config.has_agent gate: as this module's docstring explains,
        # extraction already happened upstream, so assess_claims is a pure
        # mapper with no serving-endpoint dependency. Gating it on
        # AVEN_SERVING_ENDPOINT would make a fully-configured live Vector
        # Search silently fall back to demo data, since nothing sets a
        # serving endpoint for a function that no longer calls one.
        return True

    def assess_claims(
        self,
        rows: list[dict[str, Any]],
        *,
        capability: str,
        location: str | None = None,
    ) -> list[FacilityCandidate] | None:
        """Extract + score retrieved rows into candidates, or None if unavailable."""
        if not self.available():
            return None
        return [
            self._assess_row(row, capability=capability, location=location)
            for row in rows
            if _text(row.get("unique_id"))
        ]

    def _assess_row(
        self, row: dict[str, Any], *, capability: str, location: str | None
    ) -> FacilityCandidate:
        normalized = enrichment.normalize(row)
        match = _find_matching_entry(normalized, capability)
        missing_fields = list(_missing_claim_groups(normalized))

        if match is None:
            status = evidence_status(None, None)
            source_spans: tuple[str, ...] = ()
        else:
            group_key, entry = match
            receipts = _verified_receipts(row, group_key, entry)
            quality = normalized.get("data_quality", {})
            has_conflict = bool(quality.get("conflicting_claims"))
            if receipts:
                raw_field, source_text, cited_span = receipts[0]
                status = evidence_status(
                    source_text, cited_span, has_conflict=has_conflict
                )
                row_id = _text(row.get("unique_id"))
                source_spans = tuple(
                    f"{field} [{row_id}]: {span}" for field, _, span in receipts
                )
            else:
                status = evidence_status(None, None)
                source_spans = ()
                if entry.get("evidence") and "evidence_receipt" not in missing_fields:
                    missing_fields.append("evidence_receipt")

        return FacilityCandidate(
            facility_id=_text(row.get("unique_id")),
            display_name=_text(row.get("name")) or "Facility name not documented",
            capability=capability,
            evidence_status=status,
            distance_km=_straight_line_distance_km(location, row),
            facility_type=_facility_type(row),
            missing_fields=tuple(missing_fields),
            source_spans=source_spans,
            enrichment=normalized,
        )
