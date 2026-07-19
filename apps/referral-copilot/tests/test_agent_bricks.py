"""Contract tests for the Agent Bricks row -> FacilityCandidate mapper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.agent_bricks import AgentBricksClient  # noqa: E402
from src.backend.config import BackendConfig  # noqa: E402
from src.domain import EvidenceStatus  # noqa: E402


def _configured() -> BackendConfig:
    return BackendConfig(serving_endpoint="facility-extractor-endpoint")


# Two captured real-shaped rows from workspace.default.facilities_searchable.
RICH_ROW = {
    "unique_id": "patna-district-01",
    "name": "Patna District Care Centre",
    "latitude": 25.5941,
    "longitude": 85.1376,
    "address_city": "Patna",
    "operator_type": "public",
    "facility_type": "hospital",
    "raw_capability": '["daily outpatient cardiology OPD, 9am-1pm", "24-hour emergency intake"]',
    "raw_procedure": '["ECG performed on site"]',
    "raw_equipment": "[]",
    "raw_description": "ramp access at main entrance",
    "specialties": ["Cardiology", "General medicine"],
    "capabilities": [
        {
            "claim": "Outpatient cardiology consultation",
            "evidence": ["daily outpatient cardiology OPD, 9am-1pm"],
        },
        {"claim": "24-hour emergency intake", "evidence": []},
    ],
    "procedures": [{"claim": "ECG", "evidence": ["ECG performed on site"]}],
    "equipment": [],
    "facility_facts": [
        {"fact": "Wheelchair-accessible entrance", "evidence": ["ramp access at main entrance"]}
    ],
    "data_quality": {
        "has_rich_description": True,
        "conflicting_claims": [],
        "possible_merged_facility": False,
        "merge_suspicion_reason": None,
    },
}

SPARSE_ROW = {
    "unique_id": "sparse-02",
    "name": "Sparse Facility",
    "specialties": [],
    "capabilities": [],
    "procedures": [],
    "equipment": [],
    "facility_facts": [],
    "data_quality": {
        "has_rich_description": False,
        "conflicting_claims": [],
        "possible_merged_facility": False,
        "merge_suspicion_reason": None,
    },
}

CONFLICTING_ROW = {
    "unique_id": "conflicting-03",
    "name": "Conflicting Records Facility",
    "raw_capability": '["specialist clinics run on weekdays"]',
    "specialties": ["Cardiology"],
    "capabilities": [
        {"claim": "Cardiology outpatient clinic", "evidence": ["specialist clinics run on weekdays"]}
    ],
    "procedures": [],
    "equipment": [],
    "facility_facts": [],
    "data_quality": {
        "has_rich_description": True,
        "conflicting_claims": ["Bed count appears as both 40 and 120 across records."],
        "possible_merged_facility": True,
        "merge_suspicion_reason": "Two distinct addresses appear under one facility name.",
    },
}


class AvailabilityTests(unittest.TestCase):
    def test_available_without_a_serving_endpoint(self) -> None:
        # assess_claims is a pure mapper (extraction already happened
        # upstream) — it must not require AVEN_SERVING_ENDPOINT, since no live
        # Vector Search + local-data setup ever sets one for a function that
        # calls no serving endpoint.
        client = AgentBricksClient(BackendConfig())

        self.assertTrue(client.available())
        [candidate] = client.assess_claims(
            [RICH_ROW], capability="cardiology", location="Patna"
        )
        self.assertEqual(candidate.facility_id, "patna-district-01")


class MapperTests(unittest.TestCase):
    def test_matched_claim_with_evidence_is_documented(self) -> None:
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims(
            [RICH_ROW], capability="cardiology", location="Patna"
        )

        self.assertEqual(candidate.facility_id, "patna-district-01")
        self.assertEqual(candidate.display_name, "Patna District Care Centre")
        self.assertEqual(candidate.capability, "cardiology")
        self.assertEqual(candidate.evidence_status, EvidenceStatus.DOCUMENTED)
        self.assertIn("daily outpatient cardiology OPD, 9am-1pm", candidate.source_spans[0])
        self.assertAlmostEqual(candidate.distance_km, 0.0, places=2)
        self.assertEqual(candidate.facility_type, "public")
        self.assertIn("raw_capability [patna-district-01]", candidate.source_spans[0])

    def test_extracted_span_missing_from_raw_row_fails_closed(self) -> None:
        client = AgentBricksClient(_configured())
        ungrounded = dict(RICH_ROW)
        ungrounded["raw_capability"] = '["general outpatient clinic"]'

        [candidate] = client.assess_claims([ungrounded], capability="cardiology")

        self.assertEqual(candidate.evidence_status, EvidenceStatus.NOT_DOCUMENTED)
        self.assertEqual(candidate.source_spans, ())
        self.assertIn("evidence_receipt", candidate.missing_fields)

    def test_matched_claim_without_evidence_is_not_documented(self) -> None:
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims([RICH_ROW], capability="24-hour emergency intake")

        self.assertEqual(candidate.evidence_status, EvidenceStatus.NOT_DOCUMENTED)
        self.assertEqual(candidate.source_spans, ())

    def test_no_matching_claim_group_is_not_documented_never_fabricated(self) -> None:
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims([RICH_ROW], capability="dialysis")

        self.assertEqual(candidate.evidence_status, EvidenceStatus.NOT_DOCUMENTED)
        self.assertEqual(candidate.capability, "dialysis")
        self.assertEqual(candidate.source_spans, ())

    def test_conflicting_data_quality_overrides_matched_evidence(self) -> None:
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims([CONFLICTING_ROW], capability="cardiology")

        self.assertEqual(candidate.evidence_status, EvidenceStatus.CONFLICTING)

    def test_conflicting_data_quality_does_not_fabricate_an_unmatched_capability(self) -> None:
        # A facility-wide conflict must not turn an unrelated, unclaimed
        # capability into an eligible (conflicting) candidate.
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims([CONFLICTING_ROW], capability="dialysis")

        self.assertEqual(candidate.evidence_status, EvidenceStatus.NOT_DOCUMENTED)

    def test_missing_fields_lists_every_empty_claim_group(self) -> None:
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims([SPARSE_ROW], capability="cardiology")

        self.assertEqual(candidate.evidence_status, EvidenceStatus.NOT_DOCUMENTED)
        self.assertEqual(
            set(candidate.missing_fields), {"capabilities", "procedures", "equipment", "facility_facts"}
        )

    def test_enrichment_blob_is_carried_for_display(self) -> None:
        client = AgentBricksClient(_configured())

        [candidate] = client.assess_claims([RICH_ROW], capability="cardiology")

        self.assertEqual(candidate.enrichment["specialties"], ["Cardiology", "General medicine"])

    def test_rows_without_unique_id_are_skipped(self) -> None:
        client = AgentBricksClient(_configured())
        junk_row = {"name": "No id facility"}

        candidates = client.assess_claims([RICH_ROW, junk_row], capability="cardiology")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].facility_id, "patna-district-01")

    def test_multiple_rows_are_mapped_independently(self) -> None:
        client = AgentBricksClient(_configured())

        candidates = client.assess_claims([RICH_ROW, SPARSE_ROW], capability="cardiology")

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].evidence_status, EvidenceStatus.DOCUMENTED)
        self.assertEqual(candidates[1].evidence_status, EvidenceStatus.NOT_DOCUMENTED)


if __name__ == "__main__":
    unittest.main()
