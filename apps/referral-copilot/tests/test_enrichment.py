import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.demo_adapter import build_demo_options
from src.enrichment import (
    CLAIM_GROUPS,
    cautions,
    is_empty,
    iter_claims,
    normalize,
    unverified_count,
)

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


if __name__ == "__main__":
    unittest.main()
