"""Tests for concrete travel and rupee preferences."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.preferences import (  # noqa: E402
    budget_fit,
    normalize_optional_rupees,
    summarize_preferences,
)


class RupeePreferenceTests(unittest.TestCase):
    def test_optional_limits_are_normalized_without_inventing_a_budget(self) -> None:
        self.assertIsNone(normalize_optional_rupees(None))
        self.assertIsNone(normalize_optional_rupees(0))
        self.assertEqual(normalize_optional_rupees(12_500), 12_500)
        with self.assertRaises(ValueError):
            normalize_optional_rupees(-1)

    def test_unknown_prices_remain_unknown_even_when_user_enters_a_budget(self) -> None:
        result = budget_fit(
            travel_budget_rupees=2_000,
            care_budget_rupees=5_000,
            estimated_travel_cost_rupees=None,
            documented_care_cost_rupees=None,
        )

        self.assertEqual(result.travel_status, "not_confirmed")
        self.assertEqual(result.care_status, "not_confirmed")
        self.assertNotIn("within", result.summary.casefold())

    def test_documented_or_sourced_amounts_can_be_compared_to_user_limits(self) -> None:
        result = budget_fit(
            travel_budget_rupees=2_000,
            care_budget_rupees=5_000,
            estimated_travel_cost_rupees=1_200,
            documented_care_cost_rupees=6_500,
        )

        self.assertEqual(result.travel_status, "within_budget")
        self.assertEqual(result.care_status, "over_budget")

    def test_preference_summary_records_distance_modes_and_separate_budgets(self) -> None:
        summary = summarize_preferences(
            max_distance_km=120,
            travel_modes=("train", "bus"),
            travel_budget_rupees=1_500,
            care_budget_rupees=4_000,
        )

        self.assertIn("120 km", summary)
        self.assertIn("train, bus", summary)
        self.assertIn("travel budget ₹1,500", summary)
        self.assertIn("care budget ₹4,000", summary)


if __name__ == "__main__":
    unittest.main()
