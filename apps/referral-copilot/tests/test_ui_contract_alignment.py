"""Guards that app.py stays aligned with the shared UI façade.

These are not tests of the façade itself (tests/test_ui_contract.py covers that)
but of the places where app.py chose to depend on it. They fail loudly if the
view drifts back into reimplementing what the façade owns.
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.domain import SafetyBranch
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


class CanonicalValueTests(unittest.TestCase):
    """Localization must relabel controls without changing what they return.

    The domain validates urgency/travel/budget/facility against English literals
    ({"routine","soon","urgent"}, ...). If a translated label ever reaches the
    request, validate_confirmed_intake rejects every non-English submission.
    """

    def test_option_labels_translate_but_values_stay_canonical(self):
        app = _app_module()
        canonical = ["Routine", "Soon", "Urgent", "Low", "Medium", "High",
                     "Either", "Public", "Private"]
        for code in app.LANGUAGES:
            table = app.UI_COPY.get(code, {}).get("scale", {})
            self.assertEqual(
                set(table) - set(canonical),
                set(),
                f"{code} labels a value the form never offers",
            )

    def test_untranslated_values_fall_back_to_the_canonical_label(self):
        app = _app_module()
        app.st.session_state.clear()
        app.st.session_state["language"] = "en"
        label_for = app.scale_labels()
        self.assertEqual(label_for("Soon"), "Soon")
        self.assertEqual(label_for("Unmapped"), "Unmapped")


class PlanningSeamTests(unittest.TestCase):
    """app.py must plan through the façade, which is where the safety gates run.

    Calling backend.plan_routes from a view bypasses validate_confirmed_intake
    and the emergency branch entirely — the bug this seam was built to close.
    """

    def test_the_view_never_calls_the_backend_planner_directly(self):
        source = (APP_ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "backend.plan_routes(",
            source,
            "app.py calls backend.plan_routes directly; the domain safety gates "
            "would not run. Use ui_backend().confirm_and_plan() instead.",
        )

    def test_every_safety_branch_has_a_view_that_renders_it(self):
        app = _app_module()
        for branch in SafetyBranch:
            with self.subTest(branch=branch.value):
                response = SimpleNamespace(
                    safety_branch=branch.value,
                    message="Blocking message",
                    validation_errors=("Add a location before searching.",),
                )
                # Must not raise: every branch needs a rendering path.
                app.show_safety_branch(response)


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


class SimplifiedExperienceTests(unittest.TestCase):
    def test_intake_uses_concrete_inputs_instead_of_hopping_select_sliders(self):
        source = (APP_ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("st.select_slider(", source)
        self.assertIn("travel_budget_rupees", source)
        self.assertIn("care_budget_rupees", source)
        self.assertIn("max_distance_km", source)

    def test_global_emergency_entry_and_contact_footer_exist(self):
        source = (APP_ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("Need urgent emergency help?", source)
        self.assertIn("Contact us", source)

    def test_decorative_emoji_are_not_used_in_feature_tiles(self):
        app = _app_module()
        self.assertTrue(all("icon" not in tile for tile in app.FEATURE_TILES))

    def test_localized_brand_labels_are_available(self):
        app = _app_module()
        self.assertEqual(app.BRAND_LABELS["en"], "Aven")
        self.assertIn("एवेन", app.BRAND_LABELS["hi"])
        self.assertIn("एव्हन", app.BRAND_LABELS["mr"])

    def test_voice_requires_explicit_third_party_consent(self):
        source = (APP_ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("send this recording to ElevenLabs", source)


if __name__ == "__main__":
    unittest.main()
