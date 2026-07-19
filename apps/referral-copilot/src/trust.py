"""Inspectible trust receipts for claims extracted from facility records.

Trust is ordinal and evidence-based.  It is not a probability, a clinical
quality rating, or proof that a service is currently available.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .domain import EvidenceStatus


class TrustLevel(str, Enum):
    NOT_ESTABLISHED = "not_established"
    WEAK = "weak"
    SUPPORTED = "supported"
    STRONG = "strong"
    CONFLICTING = "conflicting"


@dataclass(frozen=True)
class ClaimEvidence:
    source_field: str
    source_text: str
    cited_span: str
    source_row_id: str


@dataclass(frozen=True)
class TrustAssessment:
    claim: str
    status: EvidenceStatus
    trust_level: TrustLevel
    corroborating_fields: int
    receipts: tuple[str, ...]
    contradictions: tuple[str, ...]
    missing_fields: tuple[str, ...]
    explanation: str


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _verified_receipts(evidence: Iterable[ClaimEvidence]) -> tuple[tuple[str, str], ...]:
    verified: list[tuple[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in evidence:
        field = _clean(item.source_field)
        text = _clean(item.source_text)
        span = _clean(item.cited_span)
        row_id = _clean(item.source_row_id) or "row not documented"
        if not field or not text or not span or span.casefold() not in text.casefold():
            continue
        key = (field.casefold(), row_id.casefold(), span.casefold())
        if key in seen:
            continue
        seen.add(key)
        verified.append((field, f"{field} [{row_id}]: {span}"))
    return tuple(verified)


def assess_claim(
    claim: str,
    evidence: Iterable[ClaimEvidence],
    *,
    contradictions: Iterable[str] = (),
    expected_fields: Iterable[str] = (),
) -> TrustAssessment:
    """Assess a facility claim using literal receipts across distinct fields.

    Multiple spans in the same field do not inflate corroboration.  A conflict
    always remains visible even when other fields support the claim.
    """

    normalised_claim = _clean(claim)
    verified = _verified_receipts(evidence)
    fields = tuple(dict.fromkeys(field for field, _ in verified))
    field_keys = {field.casefold() for field in fields}
    receipts = tuple(receipt for _, receipt in verified)
    conflict_notes = tuple(
        dict.fromkeys(_clean(note) for note in contradictions if _clean(note))
    )
    missing = tuple(
        dict.fromkeys(
            _clean(field)
            for field in expected_fields
            if _clean(field) and _clean(field).casefold() not in field_keys
        )
    )

    if conflict_notes:
        status = EvidenceStatus.CONFLICTING
        level = TrustLevel.CONFLICTING
        explanation = (
            f"{len(fields)} distinct source field(s) contain literal evidence, "
            "but conflicting source information must be resolved."
        )
    elif not receipts:
        status = EvidenceStatus.NOT_DOCUMENTED
        level = TrustLevel.NOT_ESTABLISHED
        explanation = "No verified literal evidence establishes this claim in the source record."
    elif len(fields) >= 3:
        status = EvidenceStatus.DOCUMENTED
        level = TrustLevel.STRONG
        explanation = "Literal evidence is corroborated across at least three distinct source fields."
    elif len(fields) == 2:
        status = EvidenceStatus.DOCUMENTED
        level = TrustLevel.SUPPORTED
        explanation = "Literal evidence is corroborated across two distinct source fields."
    else:
        status = EvidenceStatus.DOCUMENTED
        level = TrustLevel.WEAK
        explanation = "Literal evidence appears in one source field and should be double-checked."

    return TrustAssessment(
        claim=normalised_claim,
        status=status,
        trust_level=level,
        corroborating_fields=len(fields),
        receipts=receipts,
        contradictions=conflict_notes,
        missing_fields=missing,
        explanation=explanation,
    )
