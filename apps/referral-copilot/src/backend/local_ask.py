"""Local, evidence-bounded questions over the facility snapshot.

This is intentionally not a general chatbot.  It corrects small spelling
errors against terms already present in the local facility data, then returns
only counts and names read from that snapshot.  It makes no hosted model call.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from .local_search import LocalDataRetriever

_WORD = re.compile(r"[a-z][a-z0-9-]{2,}")
_COUNT = re.compile(r"\b(how many|count|number of)\b", re.I)


def _terms(row: dict[str, Any]) -> set[str]:
    values: list[str] = [str(value) for value in row.get("specialties") or []]
    for group in ("capabilities", "procedures", "equipment"):
        for item in row.get(group) or []:
            values.append(str(item.get("claim") if isinstance(item, dict) else item))
    return {word.lower() for value in values for word in _WORD.findall(value.lower())}


def _best_capability(question: str, rows: list[dict[str, Any]]) -> str | None:
    query_words = _WORD.findall(question.lower())
    vocabulary = sorted({term for row in rows for term in _terms(row)})
    if not vocabulary:
        return None
    candidates: list[tuple[float, str]] = []
    for word in query_words:
        for term in vocabulary:
            if word == term:
                candidates.append((1.0, term))
            else:
                score = SequenceMatcher(None, word, term).ratio()
                if score >= 0.82:
                    candidates.append((score, term))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


class LocalAskClient:
    def __init__(self, data: LocalDataRetriever | None = None) -> None:
        self._data = data or LocalDataRetriever()

    def available(self) -> bool:
        return self._data.available()

    def ask(self, question: str, *, conversation_id: str | None = None) -> dict[str, Any] | None:
        question = " ".join((question or "").split())
        if not question or not self.available():
            return None
        available = self._data._load()
        if not available:
            return None
        capability = _best_capability(question, available)
        if not capability:
            return {
                "answer": "I could not match that to a documented capability in this snapshot. Try a specialty, service, or procedure name.",
                "sql": None, "columns": [], "rows": [], "conversation_id": None,
            }
        result = self._data.count_matches(capability)
        if result is None:
            return None
        count, sample = result
        if not count:
            answer = f'No facilities in the local snapshot document "{capability}".'
        elif _COUNT.search(question):
            answer = f'{count} facilit{"y" if count == 1 else "ies"} in the local snapshot document "{capability}".'
        else:
            names = ", ".join(str(row.get("name") or "unnamed facility") for row in sample[:5])
            more = f" and {count - 5} more" if count > 5 else ""
            answer = f'{count} facilit{"y" if count == 1 else "ies"} document "{capability}": {names}{more}.'
        return {
            "answer": answer,
            "sql": "# local snapshot keyword match (no live Databricks)\n" + f"capability ~= {capability!r}",
            "columns": ["unique_id", "name"],
            "rows": [{"unique_id": row.get("unique_id"), "name": row.get("name")} for row in sample],
            "conversation_id": None,
        }
