"""Facility enrichment — the extractor's OUTPUT SCHEMA, made safe for the UI.

The Agent Bricks extraction step returns, per facility:

    {
      "capabilities":   [{"claim": str, "evidence": [str]}],
      "procedures":     [{"claim": str, "evidence": [str]}],
      "equipment":      [{"claim": str, "evidence": [str]}],
      "specialties":    [str],
      "facility_facts": [{"fact": str, "evidence": [str]}],
      "data_quality": {
        "has_rich_description": bool,
        "conflicting_claims": [str],
        "possible_merged_facility": bool,
        "merge_suspicion_reason": str | None
      }
    }

Model output is untrusted shape: keys go missing, lists arrive as scalars, and
evidence comes back empty. `normalize` coerces any of that into the full shape
so the UI never has to guard, and never crashes a live demo on a bad row.

Two product rules live here rather than in the view:
  * A claim with no evidence span is kept, not dropped, and marked unverified —
    hiding it would silently turn "we could not confirm" into "not there"
    (the data-desert problem), and showing it unmarked would fake a receipt.
  * data_quality is a caution surface, never a reason to suppress a facility.
"""

from __future__ import annotations

from typing import Any, Iterator

from .trust import ClaimEvidence, TrustAssessment, assess_claim

# The three claim groups share the {"claim", "evidence"} shape; facility_facts
# uses "fact" for the same slot. (group key, UI heading, text field)
CLAIM_GROUPS: tuple[tuple[str, str, str], ...] = (
    ("capabilities", "Capabilities", "claim"),
    ("procedures", "Procedures", "claim"),
    ("equipment", "Equipment", "claim"),
    ("facility_facts", "Facility facts", "fact"),
)

_EMPTY_QUALITY: dict[str, Any] = {
    "has_rich_description": False,
    "conflicting_claims": [],
    "possible_merged_facility": False,
    "merge_suspicion_reason": None,
}


def _text(value: Any) -> str:
    """Collapse any scalar to clean display text; non-scalars become empty."""
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return ""
    return " ".join(str(value).split())


def _string_list(value: Any) -> list[str]:
    """Accept a list, a bare string, or junk; always return clean strings."""
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple, set)) else [value]
    seen: list[str] = []
    for item in items:
        text = _text(item)
        if text and text not in seen:
            seen.append(text)
    return seen


def _claims(value: Any, field: str) -> list[dict[str, Any]]:
    """Normalize one claim group. Entries without claim text are dropped; entries
    without evidence are kept and flagged, per the module docstring."""
    if not isinstance(value, (list, tuple)):
        return []
    claims: list[dict[str, Any]] = []
    for entry in value:
        if isinstance(entry, dict):
            text = _text(entry.get(field) or entry.get("claim") or entry.get("fact"))
            evidence = _string_list(entry.get("evidence"))
        else:
            # Tolerate a bare string where the extractor should have sent an object.
            text, evidence = _text(entry), []
        if text:
            claims.append({field: text, "evidence": evidence, "verified": bool(evidence)})
    return claims


def _quality(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return dict(_EMPTY_QUALITY)
    reason = _text(value.get("merge_suspicion_reason"))
    return {
        "has_rich_description": bool(value.get("has_rich_description")),
        "conflicting_claims": _string_list(value.get("conflicting_claims")),
        "possible_merged_facility": bool(value.get("possible_merged_facility")),
        # The schema allows the literal string "null"/"None" from some model runs.
        "merge_suspicion_reason": reason if reason.casefold() not in {"", "null", "none"} else None,
    }


def normalize(raw: Any) -> dict[str, Any]:
    """Return the full enrichment shape from anything the extractor produced."""
    raw = raw if isinstance(raw, dict) else {}
    result: dict[str, Any] = {
        key: _claims(raw.get(key), field) for key, _, field in CLAIM_GROUPS
    }
    result["specialties"] = _string_list(raw.get("specialties"))
    result["data_quality"] = _quality(raw.get("data_quality"))
    return result


def is_empty(enrichment: dict[str, Any]) -> bool:
    """True when there is nothing extracted to show — a data desert, which the
    UI must state plainly rather than render as an empty section."""
    return not any(enrichment.get(key) for key, _, _ in CLAIM_GROUPS) and not enrichment.get(
        "specialties"
    )


def iter_claims(enrichment: dict[str, Any]) -> Iterator[tuple[str, str, list[str], bool]]:
    """Yield (heading, text, evidence, verified) across every claim group."""
    for key, heading, field in CLAIM_GROUPS:
        for entry in enrichment.get(key, []):
            yield heading, entry[field], entry["evidence"], entry["verified"]


def cautions(enrichment: dict[str, Any]) -> list[str]:
    """User-facing caution lines from data_quality, strongest concern first."""
    quality = enrichment.get("data_quality", _EMPTY_QUALITY)
    lines: list[str] = []
    conflicts = quality.get("conflicting_claims") or []
    if conflicts:
        lines.append(
            f"{len(conflicts)} detail(s) in this facility's records disagree with each other — call before travelling."
        )
    if quality.get("possible_merged_facility"):
        reason = quality.get("merge_suspicion_reason")
        lines.append(
            "These records may describe more than one facility merged into a single entry"
            + (f": {reason}" if reason else ".")
        )
    if not quality.get("has_rich_description"):
        lines.append(
            "This facility's record is sparse, so little could be extracted. That is missing information, not missing services."
        )
    return lines


def unverified_count(enrichment: dict[str, Any]) -> int:
    """How many extracted claims arrived without a literal supporting span."""
    return sum(1 for _, _, _, verified in iter_claims(enrichment) if not verified)


def _claim_evidence(enrichment: dict[str, Any], row_id: str) -> list[ClaimEvidence]:
    """Express this record's spans as trust receipts, one per literal span.

    Each claim group is a distinct source field, which is what `assess_claim`
    counts as corroboration. `source_text` is the group's combined spans, so the
    containment check confirms a span really belongs to the group it is filed
    under and drops empty or malformed entries.

    What this cannot check: the extractor hands us one flat span per claim, not
    the facility's raw record, so nothing here re-verifies a span against the
    original source text. That check belongs in the extractor (`agent_bricks`).
    """
    receipts: list[ClaimEvidence] = []
    for key, heading, field in CLAIM_GROUPS:
        entries = enrichment.get(key, [])
        group_text = " ".join(span for entry in entries for span in entry["evidence"])
        for entry in entries:
            for span in entry["evidence"]:
                receipts.append(
                    ClaimEvidence(
                        source_field=heading,
                        source_text=group_text,
                        cited_span=span,
                        source_row_id=row_id,
                    )
                )
    return receipts


def assess_record(enrichment: dict[str, Any], *, row_id: str = "") -> TrustAssessment:
    """Grade how well this facility's record is evidenced, via `src/trust.py`.

    This is a statement about the *record*, not the facility: a weak assessment
    means little was documented, never that a service is absent or poor. The
    claim is deliberately generic because we can match spans literally but
    cannot judge whether a span semantically supports a specific capability.
    """
    quality = enrichment.get("data_quality", _EMPTY_QUALITY)
    return assess_claim(
        "This facility's documented services",
        _claim_evidence(enrichment, row_id or "row not documented"),
        contradictions=quality.get("conflicting_claims") or (),
        expected_fields=[heading for _, heading, _ in CLAIM_GROUPS],
    )
