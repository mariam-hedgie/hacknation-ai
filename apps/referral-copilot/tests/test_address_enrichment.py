from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
from src.address_enrichment import AddressEnrichment, read_ledger, verified_locations, write_ledger  # noqa: E402
from src.backend.local_search import LocalDataRetriever  # noqa: E402

class AddressEnrichmentTests(unittest.TestCase):
    def test_candidate_round_trips_but_is_not_routing_data(self):
        path = Path(tempfile.mkstemp(suffix=".jsonl")[1])
        try:
            candidate = AddressEnrichment("f1", "Example Hospital", None, "Mumbai", None, None, None, "https://example.org", "Example", "contact", "2026-07-19T00:00:00+00:00")
            write_ledger(path, [candidate])
            self.assertEqual(read_ledger(path)["f1"].review_status, "candidate")
            self.assertEqual(verified_locations(path), {})
        finally: path.unlink()

    def test_verified_requires_address(self):
        with self.assertRaises(ValueError):
            AddressEnrichment("f1", "Example Hospital", None, None, None, None, None, "https://example.org", "Example", "", "2026-07-19T00:00:00+00:00", "verified")
