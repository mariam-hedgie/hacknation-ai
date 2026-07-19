"""Approved offline UI translations and a safe voice-input boundary for Aven."""

from __future__ import annotations

import os
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "mr": "मराठी",
}

_ALIASES = {
    "en": "en",
    "en-in": "en",
    "english": "en",
    "hi": "hi",
    "hi-in": "hi",
    "hindi": "hi",
    "हिंदी": "hi",
    "mr": "mr",
    "mr-in": "mr",
    "marathi": "mr",
    "मराठी": "mr",
}

_COPY = {
    "review_and_confirm": {
        "en": "Review and confirm",
        "hi": "समीक्षा करें और पुष्टि करें",
        "mr": "तपासा आणि पुष्टी करा",
    },
    "medical_safety_notice": {
        "en": "Aven helps plan access to care. It does not diagnose or replace emergency care.",
        "hi": "Aven देखभाल तक पहुँच की योजना बनाने में मदद करता है। यह निदान नहीं करता और आपातकालीन देखभाल की जगह नहीं लेता।",
        "mr": "Aven आरोग्यसेवेपर्यंत पोहोचण्याचे नियोजन करण्यात मदत करते. ते निदान करत नाही आणि आपत्कालीन सेवेची जागा घेत नाही.",
    },
    "tell_us": {
        "en": "Tell us what you need",
        "hi": "हमें बताएं कि आपको क्या चाहिए",
        "mr": "तुम्हाला काय हवे आहे ते सांगा",
    },
    "your_plan": {
        "en": "Your next-step plan",
        "hi": "आपकी अगली कार्ययोजना",
        "mr": "तुमची पुढील कृती योजना",
    },
    "call_first": {
        "en": "Call before you travel",
        "hi": "यात्रा से पहले फोन करें",
        "mr": "प्रवासापूर्वी फोन करा",
    },
    "not_confirmed": {
        "en": "We could not confirm this",
        "hi": "हम इसकी पुष्टि नहीं कर सके",
        "mr": "आम्ही याची पुष्टी करू शकलो नाही",
    },
}


@dataclass(frozen=True)
class LanguageSelection:
    code: str
    display_name: str
    used_fallback: bool = False
    fallback_message: str | None = None


@dataclass(frozen=True)
class TranslatedText:
    text: str
    language: LanguageSelection


@dataclass(frozen=True)
class VoiceProviderStatus:
    provider: str
    available: bool
    public_message: str


class TranscriptValidationError(ValueError):
    """Voice transcript was unsafe or could not be reviewed as plain text."""


def resolve_language(value: object) -> LanguageSelection:
    raw = value.strip() if isinstance(value, str) else ""
    code = _ALIASES.get(raw.casefold())
    if code:
        return LanguageSelection(code, SUPPORTED_LANGUAGES[code])
    shown = raw or "the selected language"
    return LanguageSelection(
        "en",
        SUPPORTED_LANGUAGES["en"],
        used_fallback=True,
        fallback_message=f"{shown} is not available in this demo, so Aven is using English.",
    )


def translate_core(key: str, language: object) -> TranslatedText:
    if key not in _COPY:
        raise KeyError(f"No approved translation exists for {key!r}.")
    selection = resolve_language(language)
    return TranslatedText(_COPY[key][selection.code], selection)


def _configured_secret(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold()
    return bool(normalized) and not normalized.startswith(("todo", "replace_me", "your_"))


def voice_provider_status(env: Mapping[str, str] | None = None) -> VoiceProviderStatus:
    source = os.environ if env is None else env
    available = _configured_secret(source.get("ELEVENLABS_API_KEY"))
    message = (
        "Voice input is configured; every transcript must still be reviewed as text."
        if available
        else "Voice input is unavailable; typed input remains fully supported."
    )
    return VoiceProviderStatus("ElevenLabs", available, message)


def sanitize_voice_transcript(transcript: object, *, max_length: int = 2_000) -> str:
    """Normalize an untrusted transcript without interpreting its medical meaning."""

    if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length < 1:
        raise ValueError("max_length must be a positive integer")
    if not isinstance(transcript, str):
        raise TranscriptValidationError("Voice transcript must be text.")
    if any(unicodedata.category(char) in {"Cc", "Cf"} and char not in "\n\r\t" for char in transcript):
        raise TranscriptValidationError("Voice transcript contains unsupported control characters.")
    normalized = " ".join(transcript.split())
    if not normalized:
        raise TranscriptValidationError("Voice transcript is empty.")
    if len(normalized) > max_length:
        raise TranscriptValidationError("Voice transcript is too long to review safely.")
    return normalized
