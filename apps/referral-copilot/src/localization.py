"""Approved offline UI translations and a safe voice-input boundary for Aven.

Aven has two tiers of copy, and the split is deliberate:

* **Governed copy lives here.** Safety, evidence, and trust wording — the strings
  that change what a user believes about a hospital or an emergency. Every key
  must exist in every supported language; `translate_core` raises on an unknown
  key rather than degrading, and an unsupported *language* falls back to English
  with a visible message. A view must never hardcode these.
* **Decorative copy lives in `app.py`** (`STRINGS` / `UI_COPY` / `TILE_COPY`):
  headings, hero text, tile blurbs, form labels. `tx()` falls back to English per
  key, which is the right behavior for a missing marketing string and the wrong
  behavior for a missing emergency instruction.

`tests/test_localization_coverage.py` enforces the boundary: it fails if a
governed string is hardcoded in a view.

New keys need native review before a demo — machine-drafted translations of
safety copy are not "approved" merely by being present here.
"""

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
    # --- Emergency interruption. The most safety-critical copy in the product:
    # it must never render in a language the user did not choose.
    "emergency_title": {
        "en": "Get urgent help now",
        "hi": "अभी तत्काल मदद लें",
        "mr": "आत्ताच तातडीची मदत घ्या",
    },
    "emergency_body": {
        "en": "Seek local emergency care now. Do not wait for a facility comparison.",
        "hi": "अभी स्थानीय आपातकालीन देखभाल लें। सुविधाओं की तुलना का इंतज़ार न करें।",
        "mr": "आत्ताच स्थानिक आपत्कालीन सेवा घ्या. सुविधांच्या तुलनेची वाट पाहू नका.",
    },
    "emergency_restart": {
        "en": "Start a new non-urgent request",
        "hi": "एक नया गैर-आपातकालीन अनुरोध शुरू करें",
        "mr": "नवीन तातडी नसलेली विनंती सुरू करा",
    },
    "confirm_care_setting_help": {
        "en": "Tell us the specialty or service you think you need, then confirm again. Aven plans access to care and does not diagnose.",
        "hi": "हमें बताएं कि आपको कौन सी विशेषज्ञता या सेवा चाहिए, फिर दोबारा पुष्टि करें। Aven देखभाल तक पहुंच की योजना बनाता है, निदान नहीं करता।",
        "mr": "तुम्हाला कोणती तज्ज्ञता किंवा सेवा हवी आहे ते सांगा, नंतर पुन्हा पुष्टी करा. Aven काळजी मिळवण्याचे नियोजन करते, निदान करत नाही.",
    },
    # --- Evidence status labels. docs/ui-handoff.md requires these exact words
    # everywhere, so they are governed rather than free UI copy.
    "evidence_documented": {
        "en": "Documented in facility records",
        "hi": "सुविधा रिकॉर्ड में प्रलेखित",
        "mr": "सुविधा नोंदींमध्ये नोंदवलेले",
    },
    "evidence_conflicting": {
        "en": "Details disagree — call first",
        "hi": "विवरण आपस में मेल नहीं खाते — पहले फोन करें",
        "mr": "तपशील जुळत नाहीत — आधी फोन करा",
    },
    "evidence_external": {
        "en": "Official external source",
        "hi": "आधिकारिक बाहरी स्रोत",
        "mr": "अधिकृत बाह्य स्रोत",
    },
    "evidence_user_context": {
        "en": "You told us this",
        "hi": "यह आपने हमें बताया",
        "mr": "हे तुम्ही आम्हाला सांगितले",
    },
    "what_we_could_not_confirm": {
        "en": "What we could not confirm",
        "hi": "जिसकी हम पुष्टि नहीं कर सके",
        "mr": "जे आम्ही पुष्टी करू शकलो नाही",
    },
    # --- Trust levels (src/trust.py). Deliberately describe how much of the
    # record backs a claim — never how good the facility is.
    "trust_strong": {
        "en": "Backed by several parts of the record",
        "hi": "रिकॉर्ड के कई हिस्सों से समर्थित",
        "mr": "नोंदीच्या अनेक भागांतून समर्थित",
    },
    "trust_supported": {
        "en": "Backed by two parts of the record",
        "hi": "रिकॉर्ड के दो हिस्सों से समर्थित",
        "mr": "नोंदीच्या दोन भागांतून समर्थित",
    },
    "trust_weak": {
        "en": "Backed by one part of the record — double-check",
        "hi": "रिकॉर्ड के केवल एक हिस्से से समर्थित — दोबारा जांचें",
        "mr": "नोंदीच्या फक्त एका भागातून समर्थित — पुन्हा तपासा",
    },
}

# Copy whose wording changes what a user believes about a hospital, an
# emergency, or how well a claim is evidenced. A view must never hardcode these
# (tests/test_localization_coverage.py enforces it). The remaining keys are
# navigational headings — governed and translatable, but a view may also render
# its own heading without a safety consequence.
SAFETY_CRITICAL = frozenset(
    {
        "medical_safety_notice",
        "call_first",
        "not_confirmed",
        "emergency_title",
        "emergency_body",
        "emergency_restart",
        "confirm_care_setting_help",
        "evidence_documented",
        "evidence_conflicting",
        "evidence_external",
        "evidence_user_context",
        "what_we_could_not_confirm",
        "trust_strong",
        "trust_supported",
        "trust_weak",
    }
)

# Trust levels map onto approved copy here so no view invents its own wording.
TRUST_LEVEL_KEYS = {
    "strong": "trust_strong",
    "supported": "trust_supported",
    "weak": "trust_weak",
    "not_established": "not_confirmed",
    "conflicting": "evidence_conflicting",
}

# Evidence statuses (src/domain.py EvidenceStatus + UI-only states) map onto the
# same governed strings, so a badge and a receipt can never disagree in wording.
EVIDENCE_STATUS_KEYS = {
    "documented": "evidence_documented",
    "conflicting": "evidence_conflicting",
    "not_documented": "not_confirmed",
    "external_corroborated": "evidence_external",
    "user_context": "evidence_user_context",
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
