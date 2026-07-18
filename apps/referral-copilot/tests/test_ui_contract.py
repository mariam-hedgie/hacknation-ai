"""Stable backend contract tests for the independently owned Aven UI."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

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


class PlanningContractTests(unittest.TestCase):
    def test_confirmed_request_returns_a_ui_safe_plan_shape(self) -> None:
        result = AvenUiBackend({}).confirm_and_plan(referral_payload())

        self.assertEqual(result.safety_branch, "proceed")
        self.assertEqual(len(result.options), 3)
        self.assertTrue(all(option["evidence"] for option in result.options))
        self.assertEqual(result.validation_errors, ())

    def test_emergency_never_returns_ordinary_options(self) -> None:
        payload = referral_payload() | {
            "care_task": "symptom_first",
            "capability": "",
            "urgency": "emergency",
            "emergency_warning_reported": True,
        }
        result = AvenUiBackend({}).confirm_and_plan(payload)

        self.assertEqual(result.safety_branch, "emergency")
        self.assertEqual(result.options, ())

    def test_travel_contract_exposes_labels_without_live_price_claims(self) -> None:
        rows = AvenUiBackend({}).travel_capabilities(["car", "train"])

        self.assertEqual([row["mode"] for row in rows], ["car", "train"])
        self.assertTrue(all(row["live_price_supported"] is False for row in rows))
        self.assertTrue(all(row["label"] for row in rows))


class PersistenceContractTests(unittest.TestCase):
    def test_save_list_and_reload_match_the_ui_handoff_calls(self) -> None:
        state: dict[str, object] = {}
        backend = AvenUiBackend(state)
        option = backend.confirm_and_plan(referral_payload()).options[0]

        saved = backend.save_plan(
            referral_payload(), option, ["Call before travel"], plan_id="plan-1"
        )

        self.assertEqual(backend.load_plan("plan-1"), saved)
        self.assertEqual(backend.load_saved_plans("demo-user"), (saved,))

    def test_override_stays_separate_from_facility_evidence(self) -> None:
        backend = AvenUiBackend({})
        option = backend.confirm_and_plan(referral_payload()).options[0]
        backend.save_plan(referral_payload(), option, [], plan_id="plan-1")

        updated = backend.save_override(
            "plan-1", "another-facility", "Closer to family"
        )

        self.assertEqual(updated["selected_option"], option)
        self.assertEqual(updated["user_override"]["facility_id"], "another-facility")
        self.assertEqual(updated["user_override"]["note"], "Closer to family")

    def test_feedback_is_bounded_and_does_not_change_the_plan(self) -> None:
        backend = AvenUiBackend({})
        option = backend.confirm_and_plan(referral_payload()).options[0]
        original = backend.save_plan(referral_payload(), option, [], plan_id="plan-1")

        feedback = backend.save_feedback("plan-1", "needs_correction", "Price differed")

        self.assertEqual(feedback["status"], "needs_correction")
        self.assertEqual(backend.load_plan("plan-1"), original)
        with self.assertRaises(ValueError):
            backend.save_feedback("plan-1", "five_stars", "")


class ServiceAndCopyContractTests(unittest.TestCase):
    def test_status_reports_modes_without_secret_values(self) -> None:
        secret = "private-secret-value"
        status = AvenUiBackend(
            {},
            env={
                "GOOGLE_MAPS_API_KEY": secret,
                "ELEVENLABS_API_KEY": secret,
            },
        ).service_status()

        self.assertEqual(status["map_provider"], "google")
        self.assertTrue(status["voice_available"])
        self.assertNotIn(secret, repr(status))

    def test_approved_copy_preserves_visible_language_fallback(self) -> None:
        translated = AvenUiBackend({}).copy("review_and_confirm", "French")

        self.assertEqual(translated["text"], "Review and confirm")
        self.assertTrue(translated["used_fallback"])
        self.assertIn("French", translated["fallback_message"])


if __name__ == "__main__":
    unittest.main()
