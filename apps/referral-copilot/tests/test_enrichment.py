import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.demo_adapter import build_demo_options
from src.domain import EvidenceStatus
from src.enrichment import (
    CLAIM_GROUPS,
    assess_record,
    cautions,
    is_empty,
    iter_claims,
    normalize,
    unverified_count,
)
from src.trust import TrustLevel

FULL = {
    "capabilities": [{"claim": "Outpatient cardiology", "evidence": ["daily cardiology OPD"]}],
    "procedures": [{"claim": "ECG", "evidence": ["ECG on site"]}],
    "equipment": [{"claim": "Echo machine", "evidence": []}],
    "specialties": ["Cardiology", "Cardiology", "General medicine"],
    "facility_facts": [{"fact": "Ramp access", "evidence": ["ramp at entrance"]}],
    "data_quality": {
        "has_rich_description": True,
        "conflicting_claims": ["Bed count differs across records."],
        "possible_merged_facility": True,
        "merge_suspicion_reason": "Two addresses under one name.",
    },
}


class NormalizeTests(unittest.TestCase):
    def test_returns_every_schema_key_for_empty_input(self):
        data = normalize(None)
        for key, _, _ in CLAIM_GROUPS:
            self.assertEqual(data[key], [])
        self.assertEqual(data["specialties"], [])
        self.assertEqual(
            set(data["data_quality"]),
            {"has_rich_description", "conflicting_claims", "possible_merged_facility", "merge_suspicion_reason"},
        )

    def test_preserves_claims_evidence_and_specialties(self):
        data = normalize(FULL)
        self.assertEqual(data["capabilities"][0]["claim"], "Outpatient cardiology")
        self.assertEqual(data["capabilities"][0]["evidence"], ["daily cardiology OPD"])
        self.assertEqual(data["facility_facts"][0]["fact"], "Ramp access")
        self.assertEqual(data["specialties"], ["Cardiology", "General medicine"])

    def test_keeps_unevidenced_claims_but_marks_them_unverified(self):
        data = normalize(FULL)
        self.assertTrue(data["capabilities"][0]["verified"])
        self.assertFalse(data["equipment"][0]["verified"])
        self.assertEqual(unverified_count(data), 1)

    def test_survives_malformed_extractor_output(self):
        data = normalize(
            {
                "capabilities": "Cardiology",  # object expected, string given
                "procedures": [{"claim": "", "evidence": ["orphan span"]}],  # no claim text
                "equipment": None,
                "specialties": "Radiology",  # list expected, string given
                "data_quality": "broken",
            }
        )
        self.assertEqual(data["capabilities"], [])  # a non-list group is dropped whole
        self.assertEqual(data["procedures"], [])  # a claim with no text is dropped
        self.assertEqual(data["specialties"], ["Radiology"])
        self.assertFalse(data["data_quality"]["possible_merged_facility"])

    def test_tolerates_a_bare_string_claim_and_flags_it_unverified(self):
        data = normalize({"capabilities": ["Cardiology"]})
        self.assertEqual(data["capabilities"][0]["claim"], "Cardiology")
        self.assertFalse(data["capabilities"][0]["verified"])

    def test_treats_a_null_string_merge_reason_as_no_reason(self):
        self.assertIsNone(
            normalize({"data_quality": {"merge_suspicion_reason": "null"}})["data_quality"][
                "merge_suspicion_reason"
            ]
        )

    def test_iterates_claims_across_all_groups(self):
        headings = {heading for heading, _, _, _ in iter_claims(normalize(FULL))}
        self.assertEqual(headings, {"Capabilities", "Procedures", "Equipment", "Facility facts"})

    def test_is_empty_only_when_nothing_was_extracted(self):
        self.assertTrue(is_empty(normalize({"data_quality": {"has_rich_description": False}})))
        self.assertFalse(is_empty(normalize(FULL)))


class CautionTests(unittest.TestCase):
    def test_reports_conflicts_and_merge_suspicion_with_its_reason(self):
        lines = cautions(normalize(FULL))
        self.assertTrue(any("disagree" in line for line in lines))
        self.assertTrue(any("Two addresses under one name." in line for line in lines))

    def test_frames_a_sparse_record_as_missing_data_not_missing_services(self):
        lines = cautions(normalize({"data_quality": {"has_rich_description": False}}))
        joined = " ".join(lines).lower()
        self.assertIn("not missing services", joined)
        self.assertNotIn("does not offer", joined)

    def test_a_rich_clean_record_raises_no_caution(self):
        self.assertEqual(cautions(normalize({"data_quality": {"has_rich_description": True}})), [])


class DemoOptionTests(unittest.TestCase):
    def test_every_demo_option_carries_a_normalized_enrichment_payload(self):
        for option in build_demo_options({"care_task": "known_referral", "capability": "cardiology"}):
            self.assertIn("enrichment", option)
            self.assertIn("data_quality", option["enrichment"])

    def test_demo_data_exercises_the_states_the_card_must_render(self):
        options = build_demo_options({"care_task": "known_referral", "capability": "cardiology"})
        quality = [option["enrichment"]["data_quality"] for option in options]
        self.assertTrue(any(not q["has_rich_description"] for q in quality))
        self.assertTrue(any(q["conflicting_claims"] for q in quality))
        self.assertTrue(any(q["possible_merged_facility"] for q in quality))


class TrustIntegrationTests(unittest.TestCase):
    """assess_record is the seam between the extractor schema and src/trust.py."""

    def test_a_conflict_outranks_otherwise_good_evidence(self):
        # FULL has spans across three groups *and* a conflicting claim.
        assessment = assess_record(normalize(FULL))
        self.assertEqual(assessment.trust_level, TrustLevel.CONFLICTING)
        self.assertEqual(assessment.status, EvidenceStatus.CONFLICTING)
        self.assertTrue(assessment.contradictions)

    def test_corroboration_counts_distinct_groups_not_repeated_spans(self):
        one_group = {
            "capabilities": [
                {"claim": "Cardiology", "evidence": ["span one", "span two", "span three"]}
            ],
            "data_quality": {"has_rich_description": True, "conflicting_claims": []},
        }
        assessment = assess_record(normalize(one_group))
        self.assertEqual(assessment.corroborating_fields, 1)
        self.assertEqual(assessment.trust_level, TrustLevel.WEAK)

    def test_more_groups_raise_the_level(self):
        three_groups = {
            "capabilities": [{"claim": "Cardiology", "evidence": ["cardiology OPD"]}],
            "procedures": [{"claim": "ECG", "evidence": ["ECG on site"]}],
            "equipment": [{"claim": "Echo", "evidence": ["echo installed"]}],
            "data_quality": {"has_rich_description": True, "conflicting_claims": []},
        }
        assessment = assess_record(normalize(three_groups))
        self.assertEqual(assessment.corroborating_fields, 3)
        self.assertEqual(assessment.trust_level, TrustLevel.STRONG)

    def test_a_record_with_no_spans_is_not_established(self):
        assessment = assess_record(normalize({"capabilities": [{"claim": "X", "evidence": []}]}))
        self.assertEqual(assessment.trust_level, TrustLevel.NOT_ESTABLISHED)
        self.assertEqual(assessment.status, EvidenceStatus.NOT_DOCUMENTED)

    def test_groups_without_a_span_are_reported_as_missing_not_absent(self):
        assessment = assess_record(normalize(FULL))
        # Equipment has a claim but no evidence span in FULL.
        self.assertIn("Equipment", assessment.missing_fields)

    def test_every_seeded_demo_option_can_be_assessed(self):
        for option in build_demo_options({"capability": "cardiology"}):
            with self.subTest(facility=option["facility"]):
                assessment = assess_record(normalize(option["enrichment"]))
                self.assertIn(assessment.trust_level, set(TrustLevel))
                self.assertTrue(assessment.explanation)


if __name__ == "__main__":
    unittest.main()
