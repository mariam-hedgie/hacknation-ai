"""Local NL-question answering — the Genie seam's stand-in when there is no
live Databricks connection.

Uses an LLM (OpenAI) for exactly one job: turning a free-text question into a
small structured filter (a capability/procedure/specialty keyword, plus
whether it's a count-style question). It never writes the final answer from
its own "knowledge" — the count, the facility names, and the answer text are
all read straight back out of data/facilities_searchable.json via
LocalDataRetriever, so nothing about a real facility can be hallucinated.
This mirrors what Genie actually does (NL -> SQL -> execute -> real rows),
with a local JSON file standing in for the warehouse until this table is on
Databricks (see download_facilities.py / TODO.md P0.2). Returns None on any
failure — same fallback contract as every other seam here.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .local_search import LocalDataRetriever

_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "You turn a healthcare-facility data question into a JSON filter. "
    'Return ONLY JSON: {"capability": "<short singular lowercase keyword such as '
    '\'dialysis\' or \'cardiology\', or null if the question names none>", '
    '"is_count_question": true|false}. '
    "Extract the single clinical capability, procedure, or specialty being asked "
    "about. Do not answer the question itself — only extract the filter."
)


def _clean_key(value: str | None) -> str:
    text = (value or "").strip()
    return "" if not text or text.upper().startswith("TODO") else text


_UNSET = object()


class LocalAskClient:
    def __init__(self, data: LocalDataRetriever | None = None, *, api_key: str | None = _UNSET) -> None:  # type: ignore[assignment]
        self._data = data or LocalDataRetriever()
        # `None`/omitted -> read the environment; an explicit "" means "no key"
        # and must not silently fall back (tests rely on this to disable the
        # client deterministically regardless of what's in the environment).
        self._api_key = _clean_key(os.environ.get("OPENAI_API_KEY")) if api_key is _UNSET else _clean_key(api_key)
        self._client: Any = None
        self._client_load_attempted = False

    def available(self) -> bool:
        return bool(self._api_key) and self._data.available()

    def _client_instance(self) -> Any:
        if self._client is not None:
            return self._client
        if self._client_load_attempted:
            return None
        self._client_load_attempted = True
        try:
            from openai import OpenAI  # local import: optional dependency

            self._client = OpenAI(api_key=self._api_key)
        except Exception:
            self._client = None
        return self._client

    def _interpret(self, question: str) -> dict[str, Any] | None:
        client = self._client_instance()
        if client is None:
            return None
        try:
            response = client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            parsed = json.loads(response.choices[0].message.content)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def ask(self, question: str, *, conversation_id: str | None = None) -> dict[str, Any] | None:
        question = (question or "").strip()
        if not self.available() or not question:
            return None

        filter_ = self._interpret(question)
        if filter_ is None:
            return None

        capability = (filter_.get("capability") or "").strip()
        if not capability:
            return {
                "answer": (
                    "I could not identify a specific capability, procedure, or specialty in "
                    'that question. Try asking about one directly, e.g. "how many facilities '
                    'document dialysis?"'
                ),
                "sql": None,
                "columns": [],
                "rows": [],
                "conversation_id": None,
            }

        result = self._data.count_matches(capability)
        if result is None:
            return None
        count, sample = result

        if not count:
            answer = f'No facilities in the local snapshot document "{capability}".'
        elif filter_.get("is_count_question"):
            answer = f'{count} facilit{"y" if count == 1 else "ies"} in the local snapshot document "{capability}".'
        else:
            names = ", ".join(r.get("name") or "unnamed facility" for r in sample[:5])
            more = f" and {count - 5} more" if count > 5 else ""
            answer = f'{count} facilit{"y" if count == 1 else "ies"} document "{capability}": {names}{more}.'

        return {
            "answer": answer,
            "sql": (
                "# local keyword match over data/facilities_searchable.json (no live Databricks)\n"
                f"capability ~= {capability!r}"
            ),
            "columns": ["unique_id", "name"],
            "rows": [{"unique_id": r.get("unique_id"), "name": r.get("name")} for r in sample],
            "conversation_id": None,
        }
