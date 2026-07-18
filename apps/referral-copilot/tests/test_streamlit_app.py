"""Streamlit user-journey checks for Aven's no-key golden path."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_FILE = Path(__file__).resolve().parents[1] / "app.py"
if str(APP_FILE.parent) not in sys.path:
    sys.path.insert(0, str(APP_FILE.parent))

from src.app_logic import evaluate_demo_request  # noqa: E402


def widget_with_label(widgets, label: str):
    return next(widget for widget in widgets if widget.label == label)


class StreamlitGoldenPathTests(unittest.TestCase):
    def test_known_referral_can_be_confirmed_and_render_three_demo_options(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run(timeout=20)
        self.assertEqual(app.exception, [])

        app.text_area[0].input("I need a cardiology referral").run()
        widget_with_label(app.text_input, "A little more detail").input("cardiology")
        widget_with_label(app.text_input, "Starting city, district, or pincode").input("Patna")
        widget_with_label(app.button, "Review what Aven understood").click().run()

        self.assertIn("Review and confirm", [item.value for item in app.subheader])
        confirm = widget_with_label(app.button, "Confirm and find routes")
        self.assertFalse(confirm.disabled)
        # Streamlit's AppTest retains disappeared form widgets across an
        # explicit st.rerun, so exercise the result screen in a fresh harness
        # with the exact confirmed outcome produced above.
        results = AppTest.from_file(str(APP_FILE))
        results.session_state["stage"] = "results"
        results.session_state["selected_language"] = "en"
        results.session_state["saved_plan_ids"] = []
        results.session_state["active_plan_id"] = None
        results.session_state["request"] = app.session_state["request"]
        results.session_state["outcome"] = evaluate_demo_request(
            app.session_state["request"]
        )
        results.run(timeout=20)

        self.assertEqual(results.exception, [])
        self.assertIn("Your next-step plan", [item.value for item in results.subheader])
        card_titles = [item.value for item in results.markdown if item.value.startswith("### ")]
        self.assertIn("### Best documented fit", card_titles)
        self.assertIn("### Lower-burden route", card_titles)
        self.assertIn("### Alternative to verify", card_titles)

    def test_emergency_check_blocks_ordinary_results(self) -> None:
        app = AppTest.from_file(str(APP_FILE)).run(timeout=20)
        widget_with_label(
            app.checkbox, "I may have an emergency warning sign or need immediate help"
        ).check().run()

        self.assertTrue(any("Get urgent help now" in item.value for item in app.error))
        self.assertFalse(any("Confirm and find routes" == item.label for item in app.button))


if __name__ == "__main__":
    unittest.main()
