"""Availability labels must match the active evidence pipeline."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.config import BackendConfig  # noqa: E402


class BackendModeTests(unittest.TestCase):
    def test_vector_search_is_sufficient_for_live_evidence_mode(self) -> None:
        config = BackendConfig(
            vector_search_endpoint="aven-facility-search",
            vector_search_index="workspace.default.facilities_searchable_index",
        )

        self.assertEqual(config.mode(), "live")

    def test_partial_vector_search_configuration_stays_demo(self) -> None:
        self.assertEqual(
            BackendConfig(vector_search_endpoint="aven-facility-search").mode(),
            "demo",
        )


if __name__ == "__main__":
    unittest.main()
