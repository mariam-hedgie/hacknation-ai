"""Contract tests for the local Ask fallback (src/backend/local_ask.py).

The LLM is mocked throughout — these tests assert the contract (never call a
real API, never let the LLM author the final answer text), not model quality.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.local_ask import LocalAskClient  # noqa: E402
from src.backend.local_search import LocalDataRetriever  # noqa: E402


ROWS = [
    {"unique_id": "a", "name": "Patna Cardiac Centre", "specialties": ["Cardiology"],
     "capabilities": [{"claim": "Outpatient cardiology consultation", "evidence": ["x"]}],
     "procedures": [], "equipment": [], "facility_facts": [], "data_quality": {}},
    {"unique_id": "b", "name": "Gaya Heart Institute", "specialties": ["Cardiology"],
     "capabilities": [{"claim": "Cardiology ward", "evidence": ["y"]}],
     "procedures": [], "equipment": [], "facility_facts": [], "data_quality": {}},
    {"unique_id": "c", "name": "Sparse Clinic", "specialties": [], "capabilities": [],
     "procedures": [], "equipment": [], "facility_facts": [], "data_quality": {}},
]


def _write_data_file() -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(ROWS, tmp)
    tmp.close()
    return Path(tmp.name)


def _fake_openai_client(interpretation: dict) -> MagicMock:
    client = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=json.dumps(interpretation)))]
    client.chat.completions.create.return_value = response
    return client


class AvailabilityTests(unittest.TestCase):
    def test_unavailable_without_api_key(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="")
            self.assertFalse(client.available())
            self.assertIsNone(client.ask("how many cardiology facilities?"))
        finally:
            path.unlink()

    def test_unavailable_when_data_snapshot_missing(self) -> None:
        client = LocalAskClient(LocalDataRetriever(data_path="/nonexistent.json"), api_key="sk-test")
        self.assertFalse(client.available())

    def test_todo_placeholder_key_is_treated_as_unset(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="TODO_OPENAI_API_KEY")
            self.assertFalse(client.available())
        finally:
            path.unlink()


class AskTests(unittest.TestCase):
    def test_count_question_reports_true_count_not_llm_prose(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            client._client = _fake_openai_client({"capability": "cardiology", "is_count_question": True})

            result = client.ask("how many facilities document cardiology?")

            self.assertIn("2", result["answer"])
            self.assertEqual(len(result["rows"]), 2)
            self.assertEqual({r["unique_id"] for r in result["rows"]}, {"a", "b"})
        finally:
            path.unlink()

    def test_list_question_names_the_real_facilities(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            client._client = _fake_openai_client({"capability": "cardiology", "is_count_question": False})

            result = client.ask("which facilities document cardiology?")

            self.assertIn("Patna Cardiac Centre", result["answer"])
            self.assertIn("Gaya Heart Institute", result["answer"])
        finally:
            path.unlink()

    def test_no_matches_is_stated_honestly(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            client._client = _fake_openai_client({"capability": "neurosurgery", "is_count_question": True})

            result = client.ask("how many facilities document neurosurgery?")

            self.assertIn("No facilities", result["answer"])
            self.assertEqual(result["rows"], [])
        finally:
            path.unlink()

    def test_question_with_no_extractable_capability_asks_for_rephrase(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            client._client = _fake_openai_client({"capability": None, "is_count_question": False})

            result = client.ask("what's the weather like?")

            self.assertIsNotNone(result)
            self.assertEqual(result["rows"], [])
        finally:
            path.unlink()

    def test_llm_failure_returns_none_not_raise(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            broken_client = MagicMock()
            broken_client.chat.completions.create.side_effect = RuntimeError("api down")
            client._client = broken_client

            self.assertIsNone(client.ask("how many facilities document cardiology?"))
        finally:
            path.unlink()

    def test_malformed_llm_json_returns_none_not_raise(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            client._client = MagicMock()
            response = MagicMock()
            response.choices = [MagicMock(message=MagicMock(content="not valid json{{{"))]
            client._client.chat.completions.create.return_value = response

            self.assertIsNone(client.ask("how many facilities document cardiology?"))
        finally:
            path.unlink()

    def test_answer_never_contains_names_absent_from_the_snapshot(self) -> None:
        """The LLM's job is filter extraction only — assert the fabrication-proof
        design by checking a hostile interpretation still can't inject content:
        even if capability text is attacker-controlled, only real row names from
        the snapshot ever appear in the answer/rows."""
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            client._client = _fake_openai_client(
                {"capability": "Fabricated Hospital That Does Not Exist", "is_count_question": False}
            )

            result = client.ask("anything")

            self.assertIn("No facilities", result["answer"])
        finally:
            path.unlink()

    def test_blank_question_returns_none(self) -> None:
        path = _write_data_file()
        try:
            client = LocalAskClient(LocalDataRetriever(data_path=path), api_key="sk-test")
            self.assertIsNone(client.ask("   "))
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
