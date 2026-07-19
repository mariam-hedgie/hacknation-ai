"""Contract tests for Aven's deterministic, non-clinical routing core."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.domain import (  # noqa: E402
    EvidenceStatus,
    FacilityCandidate,
    IntakeRequest,
    SafetyBranch,
    build_shortlist,
    evidence_status,
    validate_confirmed_intake,
)


class ConfirmedIntakeTests(unittest.TestCase):
    def test_known_referral_requires_confirmation_capability_and_location(self) -> None:
        request = IntakeRequest(
            care_task="known_referral",
            confirmed_capability="cardiology",
            location="Patna",
            urgency="soon",
            travel_tolerance="medium",
            budget_sensitivity="high",
            user_confirmed=True,
        )

        self.assertEqual(validate_confirmed_intake(request), ())

    def test_unconfirmed_or_incomplete_intake_cannot_be_ranked(self) -> None:
        request = IntakeRequest(
            care_task="known_referral",
            confirmed_capability="",
            location="",
            user_confirmed=False,
        )

        errors = validate_confirmed_intake(request)
        self.assertIn("Confirm the request before searching for facilities.", errors)
        self.assertIn("Add the requested specialty, service, or procedure.", errors)
        self.assertIn("Add a location before searching for facilities.", errors)

    def test_refill_requires_existing_prescription_context(self) -> None:
        request = IntakeRequest(
            care_task="refill",
            location="Patna",
            medication_name="metformin",
            has_current_prescription=False,
            user_confirmed=True,
        )

        self.assertIn(
            "Aven can only plan a refill route when a current prescription or refill instruction is confirmed.",
            validate_confirmed_intake(request),
        )


class EvidenceStatusTests(unittest.TestCase):
    def test_evidence_status_is_documented_only_when_literal_span_exists(self) -> None:
        status = evidence_status(
            source_text="The facility provides cardiology outpatient services.",
            cited_span="cardiology outpatient services",
        )
        self.assertEqual(status, EvidenceStatus.DOCUMENTED)

    def test_evidence_status_detects_conflict_before_documentation(self) -> None:
        status = evidence_status(
            source_text="Cardiology available", cited_span="Cardiology", has_conflict=True
        )
        self.assertEqual(status, EvidenceStatus.CONFLICTING)

    def test_evidence_status_never_accepts_an_invented_citation(self) -> None:
        status = evidence_status(
            source_text="General outpatient services.", cited_span="Cardiology"
        )
        self.assertEqual(status, EvidenceStatus.NOT_DOCUMENTED)


class SafetyTests(unittest.TestCase):
    def test_emergency_warning_stops_normal_ranking(self) -> None:
        request = IntakeRequest(
            care_task="symptom_first",
            location="Patna",
            user_confirmed=True,
            emergency_warning_reported=True,
        )
        result = build_shortlist(request, [])
        self.assertEqual(result.safety_branch, SafetyBranch.EMERGENCY)
        self.assertEqual(result.options, ())

    def test_symptom_first_requires_confirmed_care_setting(self) -> None:
        request = IntakeRequest(
            care_task="symptom_first", location="Patna", user_confirmed=True
        )
        result = build_shortlist(request, [])
        self.assertEqual(result.safety_branch, SafetyBranch.CONFIRM_CARE_SETTING)
        self.assertEqual(result.options, ())


class ShortlistTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = IntakeRequest(
            care_task="known_referral",
            confirmed_capability="cardiology",
            location="Patna",
            urgency="soon",
            travel_tolerance="low",
            budget_sensitivity="high",
            facility_preference="public",
            user_confirmed=True,
        )

    def test_ranking_is_transparent_and_penalizes_conflicting_evidence(self) -> None:
        candidates = [
            FacilityCandidate(
                facility_id="near-conflict",
                display_name="Nearby Clinic",
                capability="cardiology",
                evidence_status=EvidenceStatus.CONFLICTING,
                distance_km=2,
                facility_type="public",
            ),
            FacilityCandidate(
                facility_id="far-documented",
                display_name="District Heart Centre",
                capability="cardiology",
                evidence_status=EvidenceStatus.DOCUMENTED,
                distance_km=8,
                facility_type="public",
            ),
        ]

        result = build_shortlist(self.request, candidates)

        self.assertEqual(result.safety_branch, SafetyBranch.PROCEED)
        self.assertEqual(result.options[0].candidate.facility_id, "far-documented")
        self.assertIn("documented capability evidence", result.options[0].reasons)
        self.assertIn("conflicting facility details", result.options[1].cautions)

    def test_missing_data_is_a_caution_not_a_negative_claim(self) -> None:
        candidate = FacilityCandidate(
            facility_id="unknown-contact",
            display_name="Community Hospital",
            capability="cardiology",
            evidence_status=EvidenceStatus.DOCUMENTED,
            distance_km=None,
            facility_type=None,
            missing_fields=("contact", "consultation_fee"),
        )

        result = build_shortlist(self.request, [candidate])

        self.assertIn("contact not documented", result.options[0].cautions)
        self.assertIn("consultation fee not documented", result.options[0].cautions)
        self.assertNotIn("contact unavailable", result.options[0].cautions)

    def test_only_source_backed_capability_matches_are_returned(self) -> None:
        candidates = [
            FacilityCandidate(
                facility_id="wrong-service",
                display_name="General Hospital",
                capability="general outpatient",
                evidence_status=EvidenceStatus.DOCUMENTED,
                distance_km=1,
            ),
            FacilityCandidate(
                facility_id="missing-evidence",
                display_name="Possible Heart Centre",
                capability="cardiology",
                evidence_status=EvidenceStatus.NOT_DOCUMENTED,
                distance_km=1,
            ),
        ]

        result = build_shortlist(self.request, candidates)

        self.assertEqual(result.options, ())
        self.assertEqual(result.message, "No documented facility match was found for this confirmed need.")

    def test_known_distances_beyond_the_users_maximum_are_excluded(self) -> None:
        request = IntakeRequest(
            care_task="known_referral",
            confirmed_capability="cardiology",
            location="Patna",
            max_distance_km=5,
            user_confirmed=True,
        )
        result = build_shortlist(
            request,
            [
                FacilityCandidate(
                    "near", "Nearby", "cardiology", EvidenceStatus.DOCUMENTED,
                    distance_km=4,
                ),
                FacilityCandidate(
                    "far", "Far away", "cardiology", EvidenceStatus.DOCUMENTED,
                    distance_km=12,
                ),
            ],
        )

        self.assertEqual([option.candidate.facility_id for option in result.options], ["near"])

    def test_distance_limit_excludes_a_candidate_when_distance_is_unknown(self) -> None:
        request = IntakeRequest(
            care_task="known_referral",
            confirmed_capability="cardiology",
            location="Mumbai",
            max_distance_km=5,
            user_confirmed=True,
        )

        result = build_shortlist(
            request,
            [
                FacilityCandidate(
                    "unknown-distance",
                    "City Heart Centre",
                    "cardiology",
                    EvidenceStatus.DOCUMENTED,
                    distance_km=None,
                )
            ],
        )

        self.assertEqual(result.options, ())
        self.assertIn("within 5 km", result.message)

    def test_arrival_feasibility_precedes_convenience_for_documented_matches(self) -> None:
        request = IntakeRequest(
            care_task="known_referral",
            confirmed_capability="cardiology",
            location="Patna",
            urgency="soon",
            travel_tolerance="medium",
            budget_sensitivity="medium",
            travel_budget_rupees=2_000,
            required_arrival_date="2026-07-22",
            user_confirmed=True,
        )
        candidates = [
            FacilityCandidate(
                facility_id="late",
                display_name="Late Hospital",
                capability="cardiology",
                evidence_status=EvidenceStatus.EXTERNAL_CORROBORATED,
                distance_km=4,
                estimated_journey_minutes=20,
                estimated_travel_cost_rupees=300,
                arrival_feasible=False,
            ),
            FacilityCandidate(
                facility_id="feasible",
                display_name="Reachable Hospital",
                capability="cardiology",
                evidence_status=EvidenceStatus.DOCUMENTED,
                distance_km=15,
                estimated_journey_minutes=70,
                estimated_travel_cost_rupees=1_200,
                arrival_feasible=True,
            ),
        ]

        result = build_shortlist(request, candidates)

        self.assertEqual(result.options[0].candidate.facility_id, "feasible")
        self.assertIn("can plausibly arrive by", " ".join(result.options[0].reasons))
        self.assertIn("may miss", " ".join(result.options[1].cautions))


if __name__ == "__main__":
    unittest.main()
