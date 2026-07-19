"""Genie seam — autonomous, multi-step data tasks (NL -> governed SQL).

Optional to the core Referral Copilot flow, but part of the required stack.
Useful for planner-style questions ("how many documented ICUs within 50km of
Patna?") and for regional coverage aggregates. Returns None when unavailable.
"""

from __future__ import annotations

from typing import Any

from .config import BackendConfig


class GenieClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        return self._config.has_genie

    def ask(self, question: str) -> dict[str, Any] | None:
        """Answer a natural-language data question, or None if unavailable.

        TODO(genie):
          - Start a Genie conversation against the facility tables' space
            (self._config.genie_space_id), send `question`, poll for the result,
            and return {"answer": ..., "sql": ..., "rows": [...]} so the UI can
            show the generated SQL as part of the evidence trail.
        """
        if not self.available():
            return None
        return None  # not implemented yet
