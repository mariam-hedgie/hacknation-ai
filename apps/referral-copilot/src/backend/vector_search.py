"""Mosaic AI Vector Search seam — high-speed retrieval across the 10k rows.

Returns raw candidate facility rows for a capability near a location. The rows
are noisy claims, not facts; scoring/trust happens in `agent_bricks`. Returns
None when unavailable so the service falls back to seeded demo options.

Queries `workspace.default.facilities_searchable` (Model B — see TODO.md
"Decision — Model B adopted"), one row per facility, columns matching
`src/enrichment.py`'s extractor output schema.
"""

from __future__ import annotations

from typing import Any

from .config import BackendConfig

_COLUMNS = (
    "unique_id",
    "name",
    "specialties",
    "capabilities",
    "procedures",
    "equipment",
    "facility_facts",
    "data_quality",
    "raw_description",
    "raw_capability",
    "raw_procedure",
    "raw_equipment",
    "latitude",
    "longitude",
    "address_city",
    "facility_type",
    "operator_type",
)


class VectorSearchClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._index: Any = None
        self._index_load_attempted = False

    def available(self) -> bool:
        return self._config.has_vector_search

    def _get_index(self) -> Any:
        """Build the Vector Search index handle lazily, once, on first use.

        Never runs at import time: a bad connection here must not take down
        the whole app (including demo mode). Authenticates via the Databricks
        App identity — no workspace URL or token is read from config, by
        design (see BackendConfig's docstring).
        """
        if self._index is not None:
            return self._index
        if self._index_load_attempted:
            return None
        self._index_load_attempted = True
        try:
            from databricks.vector_search.client import VectorSearchClient as DBVectorSearchClient

            client = DBVectorSearchClient()
            self._index = client.get_index(
                endpoint_name=self._config.vector_search_endpoint,
                index_name=self._config.vector_search_index,
            )
        except Exception:
            self._index = None
        return self._index

    def _rows_from_results(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        manifest = results.get("manifest") or {}
        cols = [c["name"] for c in manifest.get("columns", [])]
        data = (results.get("result") or {}).get("data_array") or []
        return [dict(zip(cols, row)) for row in data]

    def retrieve(self, capability: str, location: str | None, *, k: int = 20) -> list[dict[str, Any]] | None:
        """Return up to `k` candidate rows, or None if retrieval is unavailable.

        Keeps the raw extracted claim/evidence text; does not pre-judge claims
        here (that happens in `agent_bricks.assess_claims`).
        """
        if not self.available():
            return None
        index = self._get_index()
        if index is None:
            return None
        query_text = f"{capability} near {location}" if location else capability
        try:
            results = index.similarity_search(
                query_text=query_text,
                num_results=k,
                columns=list(_COLUMNS),
            )
        except Exception:
            return None
        return self._rows_from_results(results)
