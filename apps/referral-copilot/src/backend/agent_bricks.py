"""Agent Bricks seam — extraction, trust scoring, and self-correction.

Turns noisy retrieved rows into source-grounded `FacilityCandidate` objects with
an honest `EvidenceStatus`. This is where the brief's "Trust Scorer" lives: a
claim with no corroborating text must not read the same as one backed across
fields, and a data desert must be distinguishable from a medical desert.

Returns None when unavailable so the service falls back to seeded demo options.
"""

from __future__ import annotations

from typing import Any

from ..domain import FacilityCandidate
from .config import BackendConfig


class AgentBricksClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        return self._config.has_agent

    def assess_claims(
        self, rows: list[dict[str, Any]], *, capability: str
    ) -> list[FacilityCandidate] | None:
        """Extract + score retrieved rows into candidates, or None if unavailable.

        TODO(agent-bricks):
          - Call the served Agent Bricks / Foundation Model endpoint to extract
            the capability claim and the LITERAL supporting span (with its source
            column + row id) from each row's free text. The endpoint returns the
            extraction OUTPUT SCHEMA documented in ..enrichment; pass each row's
            response through enrichment.normalize(...) and hand it to
            FacilityCandidate.enrichment so the card can show the receipts.
          - Derive evidence_status from that payload rather than trusting it:
            data_quality.conflicting_claims -> has_conflict=True, and a claim
            whose evidence list is empty must not reach DOCUMENTED.
          - Produce an EvidenceStatus via domain.evidence_status(...) from the
            extracted span (documented / conflicting / not_documented /
            external_corroborated) — never invent capabilities (self-correction
            / Validator step, brief stretch #2).
          - Populate missing_fields honestly so "we don't know" != "not there"
            (Data Desert problem). Keep everything row-traceable.
        """
        if not self.available():
            return None
        # response = _serve(self._config.serving_endpoint, payload=rows)
        # return [domain.FacilityCandidate(... from response ...) for r in response]
        return None  # not implemented yet -> service uses demo fallback
