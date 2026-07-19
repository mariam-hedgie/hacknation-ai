"""Guards that app.py stays aligned with the shared UI façade.

These are not tests of the façade itself (tests/test_ui_contract.py covers that)
but of the places where app.py chose to depend on it. They fail loudly if the
view drifts back into reimplementing what the façade owns.
"""

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.localization import SUPPORTED_LANGUAGES, resolve_language
from src.ui_contract import _FEEDBACK_STATUSES, AvenUiBackend


def _app_module():
    """Import app.py without executing main(). Streamlit is import-safe here."""
    import importlib

    return importlib.import_module("app")


class FeedbackVocabularyTests(unittest.TestCase):
    def test_every_ui_feedback_value_is_accepted_by_the_facade(self):
        app = _app_module()
        unknown = set(app.FEEDBACK_OPTIONS.values()) - _FEEDBACK_STATUSES
        self.assertEqual(
            unknown,
            set(),
            "app.py offers feedback statuses the façade would reject; "
            "save_feedback() would raise once persistence is wired.",
        )

    def test_labels_are_distinct_so_the_selectbox_cannot_collide(self):
        app = _app_module()
        self.assertEqual(len(set(app.FEEDBACK_OPTIONS)), len(app.FEEDBACK_OPTIONS))


class LanguageTests(unittest.TestCase):
    def test_picker_offers_exactly_the_translatable_languages(self):
        app = _app_module()
        self.assertEqual(set(app.LANGUAGES), set(SUPPORTED_LANGUAGES))

    def test_every_offered_language_has_flow_strings(self):
        app = _app_module()
        for code in app.LANGUAGES:
            self.assertIn(code, app.STRINGS, f"{code} is selectable but has no STRINGS entry")

    def test_an_unsupported_language_falls_back_with_a_visible_message(self):
        selection = resolve_language("Bengali")
        self.assertEqual(selection.code, "en")
        self.assertTrue(selection.used_fallback)
        self.assertIsNotNone(selection.fallback_message)


class TravelModeTests(unittest.TestCase):
    def test_every_advertised_travel_mode_is_valid_for_the_facade(self):
        app = _app_module()
        rows = AvenUiBackend({}).travel_capabilities(app.TRAVEL_MODES)
        self.assertEqual(len(rows), len(app.TRAVEL_MODES))

    def test_offline_provider_never_claims_live_transit_or_price(self):
        app = _app_module()
        rows = AvenUiBackend({}, env={}).travel_capabilities(app.TRAVEL_MODES)
        for row in rows:
            self.assertFalse(row["live_price_supported"], row["mode"])
            self.assertFalse(row["live_transit_supported"], row["mode"])


if __name__ == "__main__":
    unittest.main()
