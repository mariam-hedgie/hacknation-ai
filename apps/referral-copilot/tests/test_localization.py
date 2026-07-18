"""Tests for Aven's offline localization and voice-input safety boundary."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src.localization import (  # noqa: E402
    SUPPORTED_LANGUAGES,
    TranscriptValidationError,
    resolve_language,
    sanitize_voice_transcript,
    translate_core,
    voice_provider_status,
)


class LanguageResolutionTests(unittest.TestCase):
    def test_supports_canonical_codes_and_human_language_names(self) -> None:
        self.assertEqual(resolve_language("en").code, "en")
        self.assertEqual(resolve_language("Hindi").code, "hi")
        self.assertEqual(resolve_language("मराठी").code, "mr")
        self.assertEqual(set(SUPPORTED_LANGUAGES), {"en", "hi", "mr"})

    def test_normalises_locale_variants_to_supported_language(self) -> None:
        selection = resolve_language("hi-IN")
        self.assertEqual(selection.code, "hi")
        self.assertFalse(selection.used_fallback)
        self.assertIsNone(selection.fallback_message)

    def test_unsupported_language_falls_back_visibly_to_english(self) -> None:
        selection = resolve_language("Bengali")
        self.assertEqual(selection.code, "en")
        self.assertTrue(selection.used_fallback)
        self.assertIn("English", selection.fallback_message or "")
        self.assertIn("Bengali", selection.fallback_message or "")

    def test_blank_language_also_has_visible_fallback_status(self) -> None:
        selection = resolve_language("  ")
        self.assertEqual(selection.code, "en")
        self.assertTrue(selection.used_fallback)
        self.assertTrue(selection.fallback_message)


class CoreTranslationTests(unittest.TestCase):
    def test_translates_core_ui_strings_in_all_supported_languages(self) -> None:
        expected = {
            "en": "Review and confirm",
            "hi": "समीक्षा करें और पुष्टि करें",
            "mr": "तपासा आणि पुष्टी करा",
        }
        for language, text in expected.items():
            with self.subTest(language=language):
                result = translate_core("review_and_confirm", language)
                self.assertEqual(result.text, text)
                self.assertEqual(result.language.code, language)

    def test_safety_copy_never_claims_diagnosis(self) -> None:
        for language in SUPPORTED_LANGUAGES:
            with self.subTest(language=language):
                result = translate_core("medical_safety_notice", language)
                self.assertTrue(result.text)
                self.assertIn(language, {"en", "hi", "mr"})
        self.assertIn("does not diagnose", translate_core("medical_safety_notice", "en").text)

    def test_unknown_copy_key_fails_closed_instead_of_inventing_translation(self) -> None:
        with self.assertRaises(KeyError):
            translate_core("diagnose_the_patient", "hi")

    def test_translation_preserves_visible_language_fallback(self) -> None:
        result = translate_core("review_and_confirm", "French")
        self.assertEqual(result.text, "Review and confirm")
        self.assertTrue(result.language.used_fallback)
        self.assertIn("French", result.language.fallback_message or "")


class VoiceProviderStatusTests(unittest.TestCase):
    def test_reports_unavailable_without_a_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            status = voice_provider_status()
        self.assertFalse(status.available)
        self.assertEqual(status.provider, "ElevenLabs")
        self.assertNotIn("key", status.public_message.casefold())

    def test_reports_available_from_environment_without_exposing_secret(self) -> None:
        secret = "sk_private_voice_secret"
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": secret}, clear=True):
            status = voice_provider_status()
        self.assertTrue(status.available)
        self.assertNotIn(secret, repr(status))
        self.assertFalse(hasattr(status, "api_key"))

    def test_explicit_config_takes_precedence_and_todo_is_not_available(self) -> None:
        status = voice_provider_status({"ELEVENLABS_API_KEY": "TODO_add_your_key"})
        self.assertFalse(status.available)


class TranscriptValidationTests(unittest.TestCase):
    def test_normalises_reviewable_voice_transcript_as_untrusted_text(self) -> None:
        self.assertEqual(
            sanitize_voice_transcript("  I need   a blood test\nnear Patna.  "),
            "I need a blood test near Patna.",
        )

    def test_rejects_blank_or_non_string_transcript(self) -> None:
        for transcript in ("   ", None, 42):
            with self.subTest(transcript=transcript):
                with self.assertRaises(TranscriptValidationError):
                    sanitize_voice_transcript(transcript)  # type: ignore[arg-type]

    def test_rejects_oversized_transcript_at_boundary(self) -> None:
        self.assertEqual(sanitize_voice_transcript("a" * 12, max_length=12), "a" * 12)
        with self.assertRaises(TranscriptValidationError):
            sanitize_voice_transcript("a" * 13, max_length=12)

    def test_rejects_control_and_format_characters(self) -> None:
        for transcript in ("safe\x00unsafe", "safe\u202eunsafe"):
            with self.subTest(transcript=repr(transcript)):
                with self.assertRaises(TranscriptValidationError):
                    sanitize_voice_transcript(transcript)

    def test_rejects_invalid_length_configuration(self) -> None:
        with self.assertRaises(ValueError):
            sanitize_voice_transcript("hello", max_length=0)


if __name__ == "__main__":
    unittest.main()
