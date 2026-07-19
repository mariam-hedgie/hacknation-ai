"""Mosaic AI Vector Search seam — high-speed retrieval across the 10k rows.

Returns raw candidate facility rows for a capability near a location. The rows
are noisy claims, not facts; scoring/trust happens in `agent_bricks`. Returns
None when unavailable so the service falls back to seeded demo options.
"""

from __future__ import annotations

from typing import Any

from .config import BackendConfig

from databricks.ai_search import VectorSearchClient as DBVectorSearchClient


class VectorSearchClient:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

        self._client = DBVectorSearchClient(
            workspace_url=config.workspace_url,
            personal_access_token=config.databricks_token,
        )

        self._index = self._client.get_index(
            endpoint_name=config.vector_search_endpoint,
            index_name=config.vector_search_index,
        )

    def available(self) -> bool:
        return self._config.has_vector_search
    
    def _rows_from_results(self, results) -> list[dict[str, Any]]:
      rows = []

      manifest = results["manifest"]
      cols = [c["name"] for c in manifest["columns"]]

      for row in results["result"]["data_array"]:
          rows.append(dict(zip(cols, row)))

      return rows

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
        
        results = self._index.similarity_search(
            query_text=f"{capability} near {location}",
            num_results=k,
            columns=[
                "unique_id",
                "name",
                "specialties",
                "capabilities",
                "procedures",
                "equipment",
                "facility_facts",
                "data_quality"
            ],
        )

        # from databricks.vector_search.client import VectorSearchClient as VSClient
        # index = VSClient().get_index(self._config.vector_search_endpoint,
        #                              self._config.vector_search_index)
        # results = index.similarity_search(query_text=capability, num_results=k,
        #     columns=["facility_id", "display_name", "capability", "procedure",
        #              "equipment", "description", "source_url", "latitude", "longitude"])
        # return _rows_from(results)
        return self._rows_from_results(results)  # not implemented yet -> service uses demo fallback
