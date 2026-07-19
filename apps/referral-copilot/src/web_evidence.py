"""Optional Tavily discovery for attributable public-source candidates.

Search results supplement the challenge data and never become ranking evidence
without a human verifying that the page is an official facility or government
source and that the literal claim appears on it.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class WebEvidenceConfigurationError(ValueError):
    pass


class WebEvidenceUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExternalSourceCandidate:
    title: str
    url: str
    snippet: str
    phone_numbers: tuple[str, ...]
    retrieved_at: str
    status: str = "external_source_candidate"


_PHONE_CANDIDATE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{6,}\d)")


def _phone_numbers(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for match in _PHONE_CANDIDATE.findall(text):
        candidate = " ".join(match.strip().split())
        digit_count = sum(character.isdigit() for character in candidate)
        if 8 <= digit_count <= 15 and candidate not in found:
            found.append(candidate)
    return tuple(found[:3])


def build_facility_query(facility: object, confirmed_capability: object) -> str:
    name = " ".join(str(facility or "").split())
    capability = " ".join(str(confirmed_capability or "").split())
    if not name or not capability:
        raise WebEvidenceConfigurationError(
            "A facility and confirmed capability are required for a public-source check."
        )
    return f'"{name}" {capability} official contact fees doctors'


def normalize_search_results(
    payload: Mapping[str, object], *, retrieved_at: str
) -> tuple[ExternalSourceCandidate, ...]:
    normalized: list[ExternalSourceCandidate] = []
    results = payload.get("results")
    if not isinstance(results, list):
        return ()
    for item in results[:3]:
        if not isinstance(item, Mapping):
            continue
        url = str(item.get("url") or "").strip()
        parsed = urlparse(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or len(url) > 2048
            or any(character.isspace() or ord(character) < 32 for character in url)
        ):
            continue
        snippet = " ".join(str(item.get("content") or "").split())[:600]
        normalized.append(
            ExternalSourceCandidate(
                title=" ".join(str(item.get("title") or parsed.netloc).split())[:200],
                url=url,
                snippet=snippet,
                phone_numbers=_phone_numbers(snippet),
                retrieved_at=retrieved_at,
            )
        )
    return tuple(normalized)


def _configured_key(env: Mapping[str, str]) -> str:
    key = (env.get("TAVILY_API_KEY") or "").strip()
    if not key or key.casefold().startswith("todo"):
        raise WebEvidenceConfigurationError("Tavily is not configured.")
    return key


def search_public_sources(
    facility: str,
    confirmed_capability: str,
    *,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 8.0,
) -> tuple[ExternalSourceCandidate, ...]:
    """Discover candidates without sending the user's narrative or location."""

    source = os.environ if env is None else env
    key = _configured_key(source)
    body = json.dumps(
        {
            "query": build_facility_query(facility, confirmed_capability),
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": 3,
            "country": "india",
        }
    ).encode("utf-8")
    request = Request(
        "https://api.tavily.com/search",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise WebEvidenceUnavailableError(
            "Public-source search is temporarily unavailable."
        ) from exc
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return normalize_search_results(payload, retrieved_at=retrieved_at)
