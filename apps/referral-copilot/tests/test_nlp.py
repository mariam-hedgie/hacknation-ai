"""Tests for review-gated local Ollama intake structuring."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.nlp import (  # noqa: E402
    IntakeNlpConfigurationError, IntakeNlpUnavailableError, OllamaIntakeClient,
    configured_nlp_client, structure_intake,
)


class RecordingIntakeClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload, self.calls = payload, []
    def extract(self, text: str, *, model: str) -> dict[str, object]:
        self.calls.append({"text": text, "model": model})
        return self.payload


class _Response:
    def __init__(self, payload: object) -> None: self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self): return json.dumps(self.payload).encode()


class OllamaIntakeTests(unittest.TestCase):
    def test_structured_output_is_normalized_and_requires_review(self) -> None:
        client = RecordingIntakeClient({"care_task": "known_referral", "capability": " cardiology ", "location": " Patna ", "urgency": "soon", "travel_modes": ["train", "spaceship"], "language": "English", "clarification_question": ""})
        result = structure_intake("I need a cardiologist near Patna", client=client)
        self.assertEqual((result.care_task, result.capability, result.location, result.travel_modes), ("known_referral", "cardiology", "Patna", ("train",)))
        self.assertTrue(result.requires_review)
        self.assertEqual(client.calls[0]["model"], "gemma3:4b")

    def test_blank_oversized_or_disabled_requests_fail_closed(self) -> None:
        with self.assertRaises(IntakeNlpConfigurationError): structure_intake("", client=RecordingIntakeClient({}))
        with self.assertRaises(IntakeNlpConfigurationError): structure_intake("x" * 2_001, client=RecordingIntakeClient({}))
        with self.assertRaises(IntakeNlpUnavailableError): structure_intake("cardiology in Patna", client=None)

    def test_disabled_or_invalid_provider_does_not_create_a_client(self) -> None:
        self.assertIsNone(configured_nlp_client({"AVEN_NLP_PROVIDER": "disabled"}))
        self.assertIsNone(configured_nlp_client({"AVEN_NLP_PROVIDER": "openai"}))
        self.assertIsNone(configured_nlp_client({"OLLAMA_HOST": "not-a-url"}))

    def test_ollama_wrapper_posts_schema_and_validates_response(self) -> None:
        payload = {"message": {"content": json.dumps({"care_task": "known_referral", "capability": "cardiology", "location": "Patna", "urgency": "soon", "travel_modes": ["train"], "language": "English", "clarification_question": None})}}
        with patch("src.nlp.urlopen", return_value=_Response(payload)) as request:
            result = OllamaIntakeClient().extract("cardiology near Patna", model="gemma3:4b")
        self.assertEqual(result["capability"], "cardiology")
        sent = json.loads(request.call_args.args[0].data.decode())
        self.assertFalse(sent["stream"])
        self.assertEqual(sent["options"]["temperature"], 0)
        self.assertIn("format", sent)


if __name__ == "__main__": unittest.main()
