"""Tests for real, review-gated OpenAI intake structuring."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.nlp import (  # noqa: E402
    IntakeNlpConfigurationError,
    IntakeNlpUnavailableError,
    OpenAIIntakeClient,
    configured_nlp_client,
    structure_intake,
)


class RecordingIntakeClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls: list[dict[str, str]] = []

    def extract(self, text: str, *, model: str) -> dict[str, object]:
        self.calls.append({"text": text, "model": model})
        return self.payload


class RecordingResponses:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def parse(self, **kwargs):
        self.kwargs = kwargs
        parsed = SimpleNamespace(
            model_dump=lambda: {
                "care_task": "known_referral",
                "capability": "cardiology",
                "location": "Patna",
                "urgency": "soon",
                "travel_modes": ["train"],
                "language": "English",
                "clarification_question": None,
            }
        )
        return SimpleNamespace(output_parsed=parsed)


class OpenAIIntakeTests(unittest.TestCase):
    def test_structured_output_is_normalized_and_requires_review(self) -> None:
        client = RecordingIntakeClient(
            {
                "care_task": "known_referral",
                "capability": "  cardiology  ",
                "location": " Patna ",
                "urgency": "soon",
                "travel_modes": ["train", "bus", "spaceship"],
                "language": "English",
                "clarification_question": "",
            }
        )

        result = structure_intake(
            "I need a cardiologist near Patna", client=client
        )

        self.assertEqual(result.care_task, "known_referral")
        self.assertEqual(result.capability, "cardiology")
        self.assertEqual(result.location, "Patna")
        self.assertEqual(result.travel_modes, ("train", "bus"))
        self.assertTrue(result.requires_review)
        self.assertEqual(client.calls[0]["model"], "gpt-5.6-sol")

    def test_blank_oversized_or_unconfigured_requests_fail_closed(self) -> None:
        client = RecordingIntakeClient({})
        with self.assertRaises(IntakeNlpConfigurationError):
            structure_intake("", client=client)
        with self.assertRaises(IntakeNlpConfigurationError):
            structure_intake("x" * 2_001, client=client)
        with self.assertRaises(IntakeNlpUnavailableError):
            structure_intake("cardiology in Patna", client=None)

    def test_placeholder_key_does_not_create_a_client(self) -> None:
        self.assertIsNone(
            configured_nlp_client({"OPENAI_API_KEY": "TODO_OPENAI_API_KEY"})
        )

    def test_openai_wrapper_uses_responses_structured_output_without_storage(self) -> None:
        responses = RecordingResponses()
        sdk = SimpleNamespace(responses=responses)
        client = OpenAIIntakeClient(sdk_client=sdk)

        result = client.extract("cardiology near Patna", model="gpt-5.6-sol")

        self.assertEqual(result["capability"], "cardiology")
        self.assertEqual(responses.kwargs["model"], "gpt-5.6-sol")
        self.assertEqual(responses.kwargs["input"], "cardiology near Patna")
        self.assertIs(responses.kwargs["store"], False)
        self.assertIn("Do not diagnose", str(responses.kwargs["instructions"]))


if __name__ == "__main__":
    unittest.main()
