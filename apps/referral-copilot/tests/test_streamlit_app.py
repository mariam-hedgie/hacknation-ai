"""Streamlit user-journey checks for Aven's no-key golden path."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_FILE = Path(__file__).resolve().parents[1] / "app.py"
if str(APP_FILE.parent) not in sys.path:
    sys.path.insert(0, str(APP_FILE.parent))

from src.ui_contract import AvenUiBackend  # noqa: E402


def referral_payload() -> dict[str, object]:
    return {
        "care_task": "known_referral",
        "capability": "cardiology",
        "location": "Patna",
        "urgency": "soon",
        "travel_tolerance": "medium",
        "budget_sensitivity": "high",
        "facility_preference": "public",
        "language": "en",
    }


class StreamlitGoldenPathTests(unittest.TestCase):
    def test_landing_screen_renders_without_a_live_service(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run(timeout=20)
        self.assertEqual(app.exception, [])

    def test_confirmed_referral_returns_three_seeded_options(self) -> None:
        response = AvenUiBackend({}).confirm_and_plan(referral_payload())

        self.assertEqual(response.safety_branch, "proceed")
        self.assertEqual(len(response.options), 3)
        self.assertTrue(all(option["evidence"] for option in response.options))

    def test_emergency_request_blocks_ordinary_results(self) -> None:
        payload = referral_payload() | {
            "care_task": "symptom_first",
            "capability": "",
            "urgency": "emergency",
            "emergency_warning_reported": True,
        }
        response = AvenUiBackend({}).confirm_and_plan(payload)

        self.assertEqual(response.safety_branch, "emergency")
        self.assertEqual(response.options, ())


if __name__ == "__main__":
    unittest.main()
