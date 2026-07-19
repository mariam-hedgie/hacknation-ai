"""Review-gated natural-language intake powered by the OpenAI Responses API.

The model structures a short user-authored request. It does not search, rank,
diagnose, or persist anything, and its output is untrusted until the user edits
and confirms the form.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field


DEFAULT_OPENAI_MODEL = "gpt-5.6-sol"
MAX_INTAKE_CHARACTERS = 2_000

_CARE_TASKS = {
    "known_referral",
    "refill",
    "lab",
    "vaccination",
    "symptom_first",
    "follow_up",
}
_URGENCY = {"routine", "soon", "urgent"}
_TRAVEL_MODES = {
    "walk",
    "bicycle",
    "motorbike",
    "car",
    "bus",
    "train",
    "taxi",
    "plane",
}


class IntakeNlpConfigurationError(ValueError):
    pass


class IntakeNlpUnavailableError(RuntimeError):
    pass


class _IntakeExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    care_task: Literal[
        "known_referral",
        "refill",
        "lab",
        "vaccination",
        "symptom_first",
        "follow_up",
    ]
    capability: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    urgency: Literal["routine", "soon", "urgent"] = "routine"
    travel_modes: list[
        Literal[
            "walk",
            "bicycle",
            "motorbike",
            "car",
            "bus",
            "train",
            "taxi",
            "plane",
        ]
    ] = Field(default_factory=list, max_length=8)
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


_INSTRUCTIONS = """You structure a care-access request for Aven.
Return only the requested schema. Do not diagnose, recommend treatment, infer a
facility capability, or claim that a service is available. Preserve the user's
own care wording. Choose symptom_first when the requested care task is unclear.
Extract a location only when the user states one. Use clarification_question for
one missing detail that the user should review. This output is a draft and will
never trigger search until the user confirms it."""


class OpenAIIntakeClient:
    """Small boundary around the official SDK, injectable for offline tests."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        sdk_client: object | None = None,
    ) -> None:
        if sdk_client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise IntakeNlpUnavailableError(
                    "Install the OpenAI Python package to enable language structuring."
                ) from exc
            sdk_client = OpenAI(
                api_key=api_key,
                timeout=15.0,
                max_retries=1,
            )
        self._client = sdk_client

    def extract(self, text: str, *, model: str) -> Mapping[str, object]:
        response = self._client.responses.parse(
            model=model,
            instructions=_INSTRUCTIONS,
            input=text,
            text_format=_IntakeExtraction,
            store=False,
        )
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise IntakeNlpUnavailableError(
                "OpenAI did not return a structured draft. Continue with the form."
            )
        return parsed.model_dump()


def _clean(value: object, *, limit: int) -> str | None:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    text = " ".join(str(value).replace("\x00", " ").split())[:limit]
    return text or None


def configured_nlp_client(
    env: Mapping[str, str] | None = None,
) -> IntakeClient | None:
    source = os.environ if env is None else env
    key = (source.get("OPENAI_API_KEY") or "").strip()
    if not key or key.casefold().startswith(("todo", "replace_me", "your_")):
        return None
    try:
        return OpenAIIntakeClient(key)
    except IntakeNlpUnavailableError:
        return None


def structure_intake(
    text: str,
    *,
    client: IntakeClient | None,
    model: str | None = None,
) -> IntakeDraft:
    normalized = " ".join(str(text or "").replace("\x00", " ").split())
    if not normalized:
        raise IntakeNlpConfigurationError(
            "Describe the care request before asking OpenAI to structure it."
        )
    if len(normalized) > MAX_INTAKE_CHARACTERS:
        raise IntakeNlpConfigurationError(
            f"Keep the request under {MAX_INTAKE_CHARACTERS:,} characters."
        )
    if client is None:
        raise IntakeNlpUnavailableError(
            "OpenAI language structuring is not configured. Continue with the form."
        )

    selected_model = (model or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip()
    try:
        raw = client.extract(normalized, model=selected_model)
    except (IntakeNlpConfigurationError, IntakeNlpUnavailableError):
        raise
    except Exception as exc:
        raise IntakeNlpUnavailableError(
            "OpenAI language structuring is temporarily unavailable. Continue with the form."
        ) from exc

    care_task = _clean(raw.get("care_task"), limit=40) or "symptom_first"
    if care_task not in _CARE_TASKS:
        care_task = "symptom_first"
    urgency = _clean(raw.get("urgency"), limit=20) or "routine"
    if urgency not in _URGENCY:
        urgency = "routine"
    supplied_modes = raw.get("travel_modes")
    modes: list[str] = []
    if isinstance(supplied_modes, (list, tuple)):
        for value in supplied_modes:
            mode = (_clean(value, limit=30) or "").casefold()
            if mode == "cycle":
                mode = "bicycle"
            if mode in _TRAVEL_MODES and mode not in modes:
                modes.append(mode)

    return IntakeDraft(
        care_task=care_task,
        capability=_clean(raw.get("capability"), limit=200),
        location=_clean(raw.get("location"), limit=200),
        urgency=urgency,
        travel_modes=tuple(modes),
        language=_clean(raw.get("language"), limit=80),
        clarification_question=_clean(raw.get("clarification_question"), limit=240),
    )
