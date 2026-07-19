"""Contracts for evidence-bounded local data questions."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))
from src.backend.local_ask import LocalAskClient  # noqa: E402
from src.backend.local_search import LocalDataRetriever  # noqa: E402

ROWS = [
    {"unique_id": "a", "name": "Patna Cardiac Centre", "specialties": ["Cardiology"], "capabilities": [{"claim": "Outpatient cardiology consultation"}], "procedures": [], "equipment": []},
    {"unique_id": "b", "name": "Gaya Heart Institute", "specialties": ["Cardiology"], "capabilities": [{"claim": "Cardiology ward"}], "procedures": [], "equipment": []},
]
def data_file():
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8"); json.dump(ROWS, tmp); tmp.close(); return Path(tmp.name)

class LocalAskTests(unittest.TestCase):
    def test_data_is_required(self):
        self.assertFalse(LocalAskClient(LocalDataRetriever(data_path="/missing.json")).available())

    def test_count_and_names_come_from_snapshot(self):
        path = data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path))
            count = client.ask("how many cardiology facilities?")
            listing = client.ask("which facilities document cardiology?")
            self.assertIn("2", count["answer"])
            self.assertIn("Patna Cardiac Centre", listing["answer"])
        finally: path.unlink()

    def test_small_misspelling_matches_documented_term(self):
        path = data_file()
        try:
            answer = LocalAskClient(LocalDataRetriever(data_path=path)).ask("how many cardiolgy facilities?")
            self.assertIn("cardiology", answer["answer"])
        finally: path.unlink()

    def test_unmatched_question_does_not_invent_an_answer(self):
        path = data_file()
        try:
            answer = LocalAskClient(LocalDataRetriever(data_path=path)).ask("what is the weather?")
            self.assertEqual(answer["rows"], [])
            self.assertIn("could not match", answer["answer"])
        finally: path.unlink()
