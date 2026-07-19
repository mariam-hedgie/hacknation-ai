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

    def test_public_brand_is_lowercase_and_promise_is_clear(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run(timeout=20)

        self.assertEqual(app.exception, [])
        self.assertTrue(any(button.label.startswith("aven") for button in app.button))
        self.assertFalse(any(button.label.startswith("Aven") for button in app.button))
        rendered = " ".join(markdown.value for markdown in app.markdown)
        self.assertIn("where to go for care", rendered.lower())
        self.assertIn("what to do next", rendered.lower())

    def test_guest_saved_plan_is_visible_from_my_plans(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run(timeout=20)
        app.session_state["profile"]["saved"] = [
            {
                "facility": "Demo District Hospital",
                "label": "Best documented fit",
                "care_task": "known_referral",
                "travel": "Seeded journey estimate",
                "next_step": "Call first to confirm the service.",
            }
        ]
        app.session_state["stage"] = "profile"
        app.run(timeout=20)

        self.assertEqual(app.exception, [])
        rendered = " ".join(markdown.value for markdown in app.markdown)
        self.assertIn("Demo District Hospital", rendered)
        self.assertIn("1 saved plan", rendered)

    def test_intake_uses_one_clear_task_selector(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run(timeout=20)
        app.session_state["stage"] = "intake"
        app.session_state["preset_care_task"] = "follow_up"
        app.run(timeout=20)

        self.assertEqual(app.exception, [])
        selector = next(
            item for item in app.selectbox if item.label == "What do you need help with?"
        )
        self.assertEqual(selector.value, "follow_up")
        rendered = " ".join(markdown.value for markdown in app.markdown)
        self.assertIn("Find a doctor", rendered)

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
