"""Review-gated, local natural-language intake for Aven.

The optional helper turns a short note into an editable form draft.  It never
searches, ranks, diagnoses, or saves data.  Ollama is contacted only through a
server-side, explicitly configured endpoint; its JSON is validated before the
browser sees it.  If it is unavailable, the normal typed form remains the
complete path.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError


DEFAULT_OLLAMA_MODEL = "gemma3:4b"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
MAX_INTAKE_CHARACTERS = 2_000

_CARE_TASKS = {"known_referral", "refill", "lab", "vaccination", "symptom_first", "follow_up"}
_URGENCY = {"routine", "soon", "urgent"}
_TRAVEL_MODES = {"walk", "bicycle", "motorbike", "car", "bus", "train", "taxi", "plane", "ambulance"}


class IntakeNlpConfigurationError(ValueError):
    pass


class IntakeNlpUnavailableError(RuntimeError):
    pass


class _IntakeExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    care_task: Literal["known_referral", "refill", "lab", "vaccination", "symptom_first", "follow_up"]
    capability: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    urgency: Literal["routine", "soon", "urgent"] = "routine"
    travel_modes: list[Literal["walk", "bicycle", "motorbike", "car", "bus", "train", "taxi", "plane", "ambulance"]] = Field(default_factory=list, max_length=8)
    language: str | None = Field(default=None, max_length=80)
    clarification_question: str | None = Field(default=None, max_length=240)


@dataclass(frozen=True)
class IntakeDraft:
    care_task: str
    capability: str | None
    location: str | None
    urgency: str
    travel_modes: tuple[str, ...]
    language: str | None
    clarification_question: str | None
    requires_review: bool = True


class IntakeClient(Protocol):
    def extract(self, text: str, *, model: str) -> Mapping[str, object]: ...


_INSTRUCTIONS = """You structure a care-access request for Aven. Return JSON matching the supplied schema only. Do not diagnose, recommend treatment, infer a facility capability, or claim that a service is available. Preserve the user's own care wording. Choose symptom_first when the care task is unclear. Extract location only when explicitly stated. Ask at most one short clarification question. The result is an editable draft and never starts a search."""


class OllamaIntakeClient:
    """Minimal server-side client for Ollama's local ``/api/chat`` endpoint."""

    def __init__(self, host: str = DEFAULT_OLLAMA_HOST, *, timeout_seconds: float = 12.0) -> None:
        host = host.strip().rstrip("/")
        if not host.startswith(("http://", "https://")):
            raise IntakeNlpConfigurationError("OLLAMA_HOST must be an http(s) URL.")
        self._host = host
        self._timeout_seconds = timeout_seconds

    def extract(self, text: str, *, model: str) -> Mapping[str, object]:
        schema = _IntakeExtraction.model_json_schema()
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": _INSTRUCTIONS},
                {"role": "user", "content": f"Schema: {json.dumps(schema, separators=(',', ':'))}\n\nRequest: {text}"},
            ],
            "format": schema,
            "stream": False,
            "options": {"temperature": 0},
        }).encode("utf-8")
        request = Request(
            f"{self._host}/api/chat", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310 - configured server endpoint
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise IntakeNlpUnavailableError("Local language structuring is unavailable.") from exc
        content = payload.get("message", {}).get("content") if isinstance(payload, dict) else None
        try:
            parsed = _IntakeExtraction.model_validate_json(content)
        except (ValidationError, TypeError) as exc:
            raise IntakeNlpUnavailableError("Local language structuring returned an invalid draft.") from exc
        return parsed.model_dump()


def _clean(value: object, *, limit: int) -> str | None:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    text = " ".join(str(value).replace("\x00", " ").split())[:limit]
    return text or None


def configured_nlp_client(env: Mapping[str, str] | None = None) -> IntakeClient | None:
    source = os.environ if env is None else env
    provider = (source.get("AVEN_NLP_PROVIDER") or "ollama").strip().casefold()
    if provider in {"", "disabled", "none"}:
        return None
    if provider != "ollama":
        return None
    try:
        return OllamaIntakeClient(source.get("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST)
    except IntakeNlpConfigurationError:
        return None


def structure_intake(text: str, *, client: IntakeClient | None, model: str | None = None) -> IntakeDraft:
    normalized = " ".join(str(text or "").replace("\x00", " ").split())
    if not normalized:
        raise IntakeNlpConfigurationError("Describe the care request before making a draft.")
    if len(normalized) > MAX_INTAKE_CHARACTERS:
        raise IntakeNlpConfigurationError(f"Keep the request under {MAX_INTAKE_CHARACTERS:,} characters.")
    if client is None:
        raise IntakeNlpUnavailableError("Language structuring is not configured. Continue with the form.")
    selected_model = (model or os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL).strip()
    try:
        raw = client.extract(normalized, model=selected_model)
    except (IntakeNlpConfigurationError, IntakeNlpUnavailableError):
        raise
    except Exception as exc:
        raise IntakeNlpUnavailableError("Language structuring is temporarily unavailable. Continue with the form.") from exc

    care_task = _clean(raw.get("care_task"), limit=40) or "symptom_first"
    urgency = _clean(raw.get("urgency"), limit=20) or "routine"
    modes: list[str] = []
    supplied_modes = raw.get("travel_modes")
    if isinstance(supplied_modes, (list, tuple)):
        for value in supplied_modes:
            mode = (_clean(value, limit=30) or "").casefold()
            if mode == "cycle":
                mode = "bicycle"
            if mode in _TRAVEL_MODES and mode not in modes:
                modes.append(mode)
    return IntakeDraft(
        care_task=care_task if care_task in _CARE_TASKS else "symptom_first",
        capability=_clean(raw.get("capability"), limit=200),
        location=_clean(raw.get("location"), limit=200),
        urgency=urgency if urgency in _URGENCY else "routine",
        travel_modes=tuple(modes),
        language=_clean(raw.get("language"), limit=80),
        clarification_question=_clean(raw.get("clarification_question"), limit=240),
    )
