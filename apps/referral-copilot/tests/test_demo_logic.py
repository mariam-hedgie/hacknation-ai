import sys
import unittest
from datetime import date, timedelta
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.demo_adapter import build_demo_options, infer_care_task, next_question


class DemoLogicTests(unittest.TestCase):
    def test_infers_refill_from_a_natural_language_request(self):
        self.assertEqual(
            infer_care_task("I need to refill my blood pressure medicine"),
            "refill",
        )

    def test_infers_lab_from_a_blood_draw_request(self):
        self.assertEqual(infer_care_task("Where can I get a blood draw?"), "lab")

    def test_returns_a_safe_default_for_an_ambiguous_request(self):
        self.assertEqual(infer_care_task("I need help"), "symptom_first")

    def test_asks_the_task_specific_first_question(self):
        self.assertIn("medicine", next_question("refill").lower())
        self.assertIn("test", next_question("lab").lower())

    def test_builds_three_transparent_options_from_a_confirmed_request(self):
        options = build_demo_options(
            {
                "care_task": "known_referral",
                "capability": "cardiology",
                "budget_sensitivity": "high",
                "travel_tolerance": "medium",
                "facility_preference": "public",
            }
        )

        self.assertEqual(len(options), 3)
        self.assertEqual(options[0]["label"], "Best documented fit")
        self.assertTrue(all(option["evidence"] for option in options))
        self.assertTrue(any("not confirmed" in option["cost"].lower() for option in options))

    def test_does_not_label_unknowns_as_unavailable(self):
        options = build_demo_options({"care_task": "lab"})
        unknown_text = " ".join(option["unknowns"].lower() for option in options)
        self.assertIn("could not confirm", unknown_text)
        self.assertNotIn("not available", unknown_text)

    def test_tight_arrival_date_changes_the_seeded_recommendation(self):
        options = build_demo_options(
            {
                "care_task": "known_referral",
                "capability": "cardiology",
                "travel_modes": ["bus"],
                "travel_budget_rupees": 2_000,
                "required_arrival_date": (date.today() + timedelta(days=1)).isoformat(),
            }
        )

        self.assertEqual(options[0]["label"], "Lower-burden route")
        self.assertTrue(options[0]["arrival_feasible"])
        self.assertIn("arrival date", options[0]["ranking"].casefold())


if __name__ == "__main__":
    unittest.main()
