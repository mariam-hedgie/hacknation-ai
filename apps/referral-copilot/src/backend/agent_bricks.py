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

Not done here (documented limit, see enrichment._claim_evidence and TODO.md
brief stretch #2 "Validator"): nothing re-verifies an extracted span against
the facility's raw record — spans are trusted as literal once `evidence_status`
confirms the span is contained in its own claim's source text.
"""

from __future__ import annotations

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


def _source_spans(group_key: str, entry: dict[str, Any]) -> tuple[str, ...]:
    return tuple(f"{group_key}: {span}" for span in entry.get("evidence", []))


def _missing_claim_groups(normalized: dict[str, Any]) -> tuple[str, ...]:
    return tuple(key for key, _, _ in enrichment.CLAIM_GROUPS if not normalized.get(key))


class AgentBricksClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        return self._config.has_agent

    def assess_claims(
        self, rows: list[dict[str, Any]], *, capability: str
    ) -> list[FacilityCandidate] | None:
        """Extract + score retrieved rows into candidates, or None if unavailable."""
        if not self.available():
            return None
        return [self._assess_row(row, capability=capability) for row in rows if _text(row.get("unique_id"))]

    def _assess_row(self, row: dict[str, Any], *, capability: str) -> FacilityCandidate:
        normalized = enrichment.normalize(row)
        match = _find_matching_entry(normalized, capability)

        if match is None:
            status = evidence_status(None, None)
            source_spans: tuple[str, ...] = ()
        else:
            group_key, entry = match
            entry_evidence = entry.get("evidence", [])
            source_text = " ".join(entry_evidence)
            cited_span = entry_evidence[0] if entry_evidence else None
            quality = normalized.get("data_quality", {})
            has_conflict = bool(quality.get("conflicting_claims"))
            status = evidence_status(source_text or None, cited_span, has_conflict=has_conflict)
            source_spans = _source_spans(group_key, entry) if status != EvidenceStatus.NOT_DOCUMENTED or has_conflict else ()

        return FacilityCandidate(
            facility_id=_text(row.get("unique_id")),
            display_name=_text(row.get("name")) or "Facility name not documented",
            capability=capability,
            evidence_status=status,
            distance_km=None,  # Model B has no lat/lon — see TODO.md Blocker #1.
            facility_type=None,  # not present in facilities_searchable.
            missing_fields=_missing_claim_groups(normalized),
            source_spans=source_spans,
            enrichment=normalized,
        )
