"""Tests for source-grounded, inspectable facility trust assessments."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.domain import EvidenceStatus  # noqa: E402
from src.trust import ClaimEvidence, TrustLevel, assess_claim  # noqa: E402


class TrustAssessmentTests(unittest.TestCase):
    def test_distinct_verified_fields_strengthen_a_claim(self) -> None:
        one_field = assess_claim(
            "cardiology",
            [
                ClaimEvidence(
                    source_field="description",
                    source_text="Cardiology services are available.",
                    cited_span="Cardiology",
                    source_row_id="row-1",
                )
            ],
        )
        three_fields = assess_claim(
            "cardiology",
            [
                ClaimEvidence("description", "Cardiology services.", "Cardiology", "row-1"),
                ClaimEvidence("procedures", "Cardiology consultation.", "Cardiology", "row-1"),
                ClaimEvidence("equipment", "Cardiology ECG unit.", "Cardiology", "row-1"),
            ],
        )

        self.assertEqual(one_field.trust_level, TrustLevel.WEAK)
        self.assertEqual(three_fields.trust_level, TrustLevel.STRONG)
        self.assertEqual(three_fields.corroborating_fields, 3)
        self.assertGreater(len(three_fields.receipts), len(one_field.receipts))

    def test_invalid_literal_span_is_not_evidence(self) -> None:
        result = assess_claim(
            "cardiology",
            [ClaimEvidence("description", "General outpatient care.", "cardiology", "row-2")],
        )

        self.assertEqual(result.status, EvidenceStatus.NOT_DOCUMENTED)
        self.assertEqual(result.trust_level, TrustLevel.NOT_ESTABLISHED)
        self.assertEqual(result.receipts, ())
        self.assertIn("literal evidence", result.explanation.casefold())

    def test_conflict_overrides_otherwise_strong_corroboration(self) -> None:
        result = assess_claim(
            "cardiology",
            [
                ClaimEvidence("description", "Cardiology services.", "Cardiology", "row-3"),
                ClaimEvidence("procedures", "Cardiology consultation.", "Cardiology", "row-3"),
                ClaimEvidence("equipment", "Cardiology ECG unit.", "Cardiology", "row-3"),
            ],
            contradictions=("A second record says the service is unavailable.",),
        )

        self.assertEqual(result.status, EvidenceStatus.CONFLICTING)
        self.assertEqual(result.trust_level, TrustLevel.CONFLICTING)
        self.assertIn("second record", result.contradictions[0].casefold())

    def test_missing_fields_are_explicit_and_do_not_become_negative_claims(self) -> None:
        result = assess_claim(
            "cardiology",
            [ClaimEvidence("description", "Cardiology services.", "Cardiology", "row-4")],
            expected_fields=("description", "procedures", "equipment"),
        )

        self.assertEqual(result.missing_fields, ("procedures", "equipment"))
        self.assertNotIn("unavailable", result.explanation.casefold())

    def test_trust_is_ordinal_not_a_fabricated_probability(self) -> None:
        result = assess_claim(
            "cardiology",
            [ClaimEvidence("description", "Cardiology services.", "Cardiology", "row-5")],
        )

        self.assertNotIn("%", result.explanation)
        self.assertFalse(hasattr(result, "confidence_probability"))


if __name__ == "__main__":
    unittest.main()
