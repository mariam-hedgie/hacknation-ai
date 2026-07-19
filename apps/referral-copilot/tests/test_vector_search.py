"""Contract tests for the Vector Search seam (src/backend/vector_search.py)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.config import BackendConfig  # noqa: E402
from src.backend.vector_search import VectorSearchClient  # noqa: E402


def _configured() -> BackendConfig:
    return BackendConfig(
        vector_search_endpoint="facility-endpoint",
        vector_search_index="workspace.default.facilities_searchable_index",
    )


class FakeIndex:
    def __init__(self, response: dict | None = None, *, raises: Exception | None = None) -> None:
        self.response = response
        self.raises = raises
        self.calls: list[dict] = []

    def similarity_search(self, **kwargs):
        self.calls.append(kwargs)
        if self.raises:
            raise self.raises
        return self.response


class VectorSearchAvailabilityTests(unittest.TestCase):
    def test_unavailable_without_endpoint_and_index(self) -> None:
        client = VectorSearchClient(BackendConfig())
        self.assertFalse(client.available())
        self.assertIsNone(client.retrieve("cardiology", "Patna"))

    def test_available_when_endpoint_and_index_configured(self) -> None:
        client = VectorSearchClient(_configured())
        self.assertTrue(client.available())


class VectorSearchLazyInitTests(unittest.TestCase):
    def test_retrieve_returns_none_when_index_build_fails(self) -> None:
        # databricks-vectorsearch is not installed in this environment, so the
        # lazy import inside _get_index fails -> caught -> None, never a crash.
        client = VectorSearchClient(_configured())

        result = client.retrieve("cardiology", "Patna")

        self.assertIsNone(result)

    def test_failed_index_build_is_not_retried_every_call(self) -> None:
        client = VectorSearchClient(_configured())

        client.retrieve("cardiology", "Patna")
        client.retrieve("cardiology", "Patna")

        self.assertTrue(client._index_load_attempted)
        self.assertIsNone(client._index)


class VectorSearchRetrieveTests(unittest.TestCase):
    def test_searchable_table_preserves_embedding_text_and_raw_receipts(self) -> None:
        pipeline = (REPO_ROOT / "flatten_data.py").read_text(encoding="utf-8")

        self.assertIn("AS search_text", pipeline)
        self.assertIn("source.capability AS raw_capability", pipeline)
        self.assertIn("source.latitude", pipeline)

    def test_retrieve_queries_configured_columns_and_parses_rows(self) -> None:
        client = VectorSearchClient(_configured())
        fake_index = FakeIndex(
            {
                "manifest": {"columns": [{"name": "unique_id"}, {"name": "name"}]},
                "result": {"data_array": [["facility-1", "Patna Demo Hospital"]]},
            }
        )
        client._get_index = lambda: fake_index  # type: ignore[method-assign]

        rows = client.retrieve("cardiology", "Patna", k=5)

        self.assertEqual(rows, [{"unique_id": "facility-1", "name": "Patna Demo Hospital"}])
        call = fake_index.calls[0]
        self.assertEqual(call["query_text"], "cardiology near Patna")
        self.assertEqual(call["num_results"], 5)
        self.assertIn("capabilities", call["columns"])
        self.assertIn("data_quality", call["columns"])
        self.assertIn("raw_capability", call["columns"])
        self.assertIn("latitude", call["columns"])
        self.assertIn("operator_type", call["columns"])

    def test_retrieve_omits_location_from_query_when_absent(self) -> None:
        client = VectorSearchClient(_configured())
        fake_index = FakeIndex({"manifest": {"columns": []}, "result": {"data_array": []}})
        client._get_index = lambda: fake_index  # type: ignore[method-assign]

        client.retrieve("cardiology", None)

        self.assertEqual(fake_index.calls[0]["query_text"], "cardiology")

    def test_retrieve_returns_none_on_query_failure(self) -> None:
        client = VectorSearchClient(_configured())
        fake_index = FakeIndex(raises=RuntimeError("endpoint unavailable"))
        client._get_index = lambda: fake_index  # type: ignore[method-assign]

        self.assertIsNone(client.retrieve("cardiology", "Patna"))

    def test_retrieve_handles_missing_manifest_or_data_array(self) -> None:
        client = VectorSearchClient(_configured())
        fake_index = FakeIndex({})
        client._get_index = lambda: fake_index  # type: ignore[method-assign]

        self.assertEqual(client.retrieve("cardiology", "Patna"), [])


if __name__ == "__main__":
    unittest.main()
