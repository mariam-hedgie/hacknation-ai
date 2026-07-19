"""Mosaic AI Vector Search seam — high-speed retrieval across the 10k rows.

Returns raw candidate facility rows for a capability near a location. The rows
are noisy claims, not facts; scoring/trust happens in `agent_bricks`. Returns
None when unavailable so the service falls back to seeded demo options.
"""

from __future__ import annotations

from typing import Any

from .config import BackendConfig


class VectorSearchClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        return self._config.has_vector_search

    def retrieve(self, capability: str, location: str | None, *, k: int = 20) -> list[dict[str, Any]] | None:
        """Return up to `k` candidate rows, or None if retrieval is unavailable.

        TODO(vector-search):
          - Build/attach a Mosaic AI Vector Search index over the 10k facility
            rows (embed `description` + `capability` + `procedure` + `equipment`).
          - Query it with the capability (and, once geocoded, the location) and
            return the matching source rows INCLUDING row ids + the literal
            source columns so downstream citations are row-level.
          - Keep the raw text; do not pre-judge claims here.
        """
        if not self.available():
            return None
        # from databricks.vector_search.client import VectorSearchClient as VSClient
        # index = VSClient().get_index(self._config.vector_search_endpoint,
        #                              self._config.vector_search_index)
        # results = index.similarity_search(query_text=capability, num_results=k,
        #     columns=["facility_id", "display_name", "capability", "procedure",
        #              "equipment", "description", "source_url", "latitude", "longitude"])
        # return _rows_from(results)
        return None  # not implemented yet -> service uses demo fallback
