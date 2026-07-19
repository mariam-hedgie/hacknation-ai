"""Tests for explicit, review-before-use voice transcription."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.voice import (  # noqa: E402
    MAX_AUDIO_BYTES,
    VoiceUnavailableError,
    configured_voice_client,
    transcribe_for_review,
)


class RecordingSpeechClient:
    def __init__(self, text: str = "I need a cardiology visit") -> None:
        self.text = text
        self.calls: list[dict[str, object]] = []

    def transcribe(self, audio: bytes, *, language_code: str | None) -> str:
        self.calls.append({"audio": audio, "language_code": language_code})
        return self.text


class VoiceTests(unittest.TestCase):
    def test_transcript_is_returned_for_review_not_automatically_submitted(self) -> None:
        client = RecordingSpeechClient()
        result = transcribe_for_review(
            b"audio-bytes", client=client, language_code="hin"
        )

        self.assertEqual(result.text, "I need a cardiology visit")
        self.assertTrue(result.requires_review)
        self.assertEqual(client.calls[0]["language_code"], "hin")

    def test_blank_audio_or_missing_client_fails_closed(self) -> None:
        with self.assertRaises(VoiceUnavailableError):
            transcribe_for_review(b"", client=RecordingSpeechClient())
        with self.assertRaises(VoiceUnavailableError):
            transcribe_for_review(b"audio", client=None)

    def test_oversized_recording_is_rejected_before_external_upload(self) -> None:
        client = RecordingSpeechClient()
        with self.assertRaises(VoiceUnavailableError):
            transcribe_for_review(b"x" * (MAX_AUDIO_BYTES + 1), client=client)
        self.assertEqual(client.calls, [])

    def test_voice_is_hidden_until_explicitly_enabled(self) -> None:
        self.assertIsNone(
            configured_voice_client(
                {"ELEVENLABS_API_KEY": "configured-but-unverified"}
            )
        )


if __name__ == "__main__":
    unittest.main()
