"""Integration contracts for the confirmed Aven user journey."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.app_logic import build_confirmed_request, evaluate_demo_request  # noqa: E402
from src.domain import SafetyBranch  # noqa: E402


class ConfirmedJourneyTests(unittest.TestCase):
    def test_form_payload_becomes_a_confirmed_domain_request(self) -> None:
        request = build_confirmed_request(
            {
                "care_task": "known_referral",
                "capability": "cardiology",
                "location": "Patna",
                "urgency": "soon",
                "travel_tolerance": "low",
                "budget_sensitivity": "high",
                "facility_preference": "public",
                "language": "hi",
            }
        )

        self.assertTrue(request.user_confirmed)
        self.assertEqual(request.confirmed_capability, "cardiology")
        self.assertEqual(request.language_preference, "hi")

    def test_emergency_report_stops_demo_option_generation(self) -> None:
        outcome = evaluate_demo_request(
            {
                "care_task": "symptom_first",
                "capability": "",
                "location": "Patna",
                "urgency": "emergency",
                "emergency_warning_reported": True,
            }
        )

        self.assertEqual(outcome.safety_branch, SafetyBranch.EMERGENCY)
        self.assertEqual(outcome.options, ())

    def test_incomplete_request_returns_errors_instead_of_seeded_results(self) -> None:
        outcome = evaluate_demo_request(
            {
                "care_task": "known_referral",
                "capability": "cardiology",
                "location": "",
            }
        )

        self.assertEqual(outcome.safety_branch, SafetyBranch.INCOMPLETE_INTAKE)
        self.assertIn("Add a location", " ".join(outcome.validation_errors))
        self.assertEqual(outcome.options, ())

    def test_refill_requires_confirmed_prescription_before_results(self) -> None:
        outcome = evaluate_demo_request(
            {
                "care_task": "refill",
                "medication_name": "metformin",
                "location": "Mumbai",
                "has_current_prescription": False,
            }
        )

        self.assertEqual(outcome.safety_branch, SafetyBranch.INCOMPLETE_INTAKE)
        self.assertEqual(outcome.options, ())

    def test_valid_request_returns_three_explicitly_seeded_options(self) -> None:
        outcome = evaluate_demo_request(
            {
                "care_task": "known_referral",
                "capability": "cardiology",
                "location": "Patna",
                "urgency": "soon",
                "travel_tolerance": "medium",
                "budget_sensitivity": "high",
                "facility_preference": "public",
            }
        )

        self.assertEqual(outcome.safety_branch, SafetyBranch.PROCEED)
        self.assertEqual(len(outcome.options), 3)
        self.assertTrue(all("demo" in option["summary"].lower() for option in outcome.options))


if __name__ == "__main__":
    unittest.main()
