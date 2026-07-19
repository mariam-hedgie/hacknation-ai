"""ElevenLabs transcription boundary with mandatory transcript review."""

from __future__ import annotations

import os
from dataclasses import dataclass
from io import BytesIO
from typing import Mapping, Protocol

from .localization import sanitize_voice_transcript


class VoiceUnavailableError(RuntimeError):
    pass


MAX_AUDIO_BYTES = 10 * 1024 * 1024


class SpeechClient(Protocol):
    def transcribe(self, audio: bytes, *, language_code: str | None) -> str: ...


@dataclass(frozen=True)
class ReviewableTranscript:
    text: str
    requires_review: bool = True


class ElevenLabsSpeechClient:
    def __init__(self, api_key: str) -> None:
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError as exc:
            raise VoiceUnavailableError(
                "Install the ElevenLabs Python package to enable transcription."
            ) from exc
        self._client = ElevenLabs(api_key=api_key)

    def transcribe(self, audio: bytes, *, language_code: str | None) -> str:
        stream = BytesIO(audio)
        stream.name = "aven-recording.wav"
        result = self._client.speech_to_text.convert(
            file=stream,
            model_id="scribe_v2",
            language_code=language_code,
            tag_audio_events=False,
        )
        return str(getattr(result, "text", ""))


def configured_voice_client(
    env: Mapping[str, str] | None = None,
) -> SpeechClient | None:
    source = os.environ if env is None else env
    key = (source.get("ELEVENLABS_API_KEY") or "").strip()
    if not key or key.casefold().startswith("todo"):
        return None
    try:
        return ElevenLabsSpeechClient(key)
    except VoiceUnavailableError:
        return None


def transcribe_for_review(
    audio: bytes,
    *,
    client: SpeechClient | None,
    language_code: str | None = None,
) -> ReviewableTranscript:
    if not audio:
        raise VoiceUnavailableError("Record audio before requesting transcription.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise VoiceUnavailableError("Keep the voice recording under 10 MB.")
    if client is None:
        raise VoiceUnavailableError("Voice transcription is not configured.")
    try:
        text = client.transcribe(audio, language_code=language_code)
    except Exception as exc:
        raise VoiceUnavailableError("Voice transcription failed. Use typed input.") from exc
    return ReviewableTranscript(sanitize_voice_transcript(text))
