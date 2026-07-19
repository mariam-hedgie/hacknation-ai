"""Contract tests for the local-file retrieval seam (src/backend/local_search.py)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.local_search import LocalDataRetriever  # noqa: E402


ROW_A = {
    "unique_id": "facility-a",
    "name": "Patna District Care Centre",
    "specialties": ["Cardiology"],
    "capabilities": [{"claim": "Outpatient cardiology consultation", "evidence": ["cardiology OPD 9am-1pm"]}],
    "procedures": [],
    "equipment": [],
    "facility_facts": [],
    "data_quality": {"has_rich_description": True, "conflicting_claims": [], "possible_merged_facility": False, "merge_suspicion_reason": None},
}

ROW_B = {
    "unique_id": "facility-b",
    "name": "Sparse Facility",
    "specialties": [],
    "capabilities": [],
    "procedures": [{"claim": "Dialysis treatment", "evidence": ["dialysis unit, 10 machines"]}],
    "equipment": [],
    "facility_facts": [],
    "data_quality": {"has_rich_description": False, "conflicting_claims": [], "possible_merged_facility": False, "merge_suspicion_reason": None},
}


def _write_data_file(records: list[dict]) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(records, tmp)
    tmp.close()
    return Path(tmp.name)


def _write_jsonl_data_file(records: list[dict]) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
    for record in records:
        tmp.write(json.dumps(record) + "\n")
    tmp.close()
    return Path(tmp.name)


class AvailabilityTests(unittest.TestCase):
    def test_unavailable_when_file_does_not_exist(self) -> None:
        client = LocalDataRetriever(data_path="/nonexistent/path/facilities.json")

        self.assertFalse(client.available())
        self.assertIsNone(client.retrieve("cardiology", None))

    def test_available_when_file_exists(self) -> None:
        path = _write_data_file([ROW_A])
        try:
            client = LocalDataRetriever(data_path=path)
            self.assertTrue(client.available())
        finally:
            path.unlink()


class RetrieveTests(unittest.TestCase):
    def test_jsonl_snapshot_decodes_nested_facility_columns(self) -> None:
        jsonl_row = {
            **ROW_A,
            "specialties": json.dumps(ROW_A["specialties"]),
            "capabilities": json.dumps(ROW_A["capabilities"]),
            "procedures": json.dumps(ROW_A["procedures"]),
            "equipment": json.dumps(ROW_A["equipment"]),
            "facility_facts": json.dumps(ROW_A["facility_facts"]),
            "data_quality": json.dumps(ROW_A["data_quality"]),
        }
        path = _write_jsonl_data_file([jsonl_row])
        try:
            client = LocalDataRetriever(data_path=path)

            rows = client.retrieve("cardiology", "Patna")

            self.assertEqual([row["unique_id"] for row in rows], ["facility-a"])
            self.assertEqual(rows[0]["capabilities"], ROW_A["capabilities"])
            self.assertEqual(rows[0]["specialties"], ROW_A["specialties"])
        finally:
            path.unlink()

    def test_matches_capability_claim_substring(self) -> None:
        path = _write_data_file([ROW_A, ROW_B])
        try:
            client = LocalDataRetriever(data_path=path)
            rows = client.retrieve("cardiology", "Patna")
            self.assertEqual([r["unique_id"] for r in rows], ["facility-a"])
        finally:
            path.unlink()

    def test_matches_procedure_claim_and_specialty_tag(self) -> None:
        path = _write_data_file([ROW_A, ROW_B])
        try:
            client = LocalDataRetriever(data_path=path)
            self.assertEqual([r["unique_id"] for r in client.retrieve("dialysis", None)], ["facility-b"])
            self.assertEqual([r["unique_id"] for r in client.retrieve("Cardiology", None)], ["facility-a"])
        finally:
            path.unlink()

    def test_unknown_location_does_not_fabricate_a_city_filter(self) -> None:
        path = _write_data_file([ROW_A])
        try:
            client = LocalDataRetriever(data_path=path)
            with_location = client.retrieve("cardiology", "Unknown place")
            without_location = client.retrieve("cardiology", None)
            self.assertEqual(with_location, without_location)
        finally:
            path.unlink()

    def test_known_city_excludes_matching_facilities_in_another_city(self) -> None:
        mumbai = {**ROW_A, "name": "Mumbai Cardiac Centre"}
        kerala = {
            **ROW_A,
            "unique_id": "facility-kerala",
            "name": "Kerala Cardiac Centre",
        }
        path = _write_data_file([mumbai, kerala])
        try:
            client = LocalDataRetriever(data_path=path)

            rows = client.retrieve("cardiology", "Mumbai, Maharashtra")

            self.assertEqual([row["unique_id"] for row in rows], ["facility-a"])
        finally:
            path.unlink()

    def test_k_caps_the_result_count(self) -> None:
        path = _write_data_file([ROW_A] * 5)
        try:
            client = LocalDataRetriever(data_path=path)
            self.assertEqual(len(client.retrieve("cardiology", None, k=2)), 2)
        finally:
            path.unlink()

    def test_blank_capability_returns_empty_list_not_none(self) -> None:
        path = _write_data_file([ROW_A])
        try:
            client = LocalDataRetriever(data_path=path)
            self.assertEqual(client.retrieve("   ", None), [])
        finally:
            path.unlink()

    def test_malformed_json_file_returns_none_not_raise(self) -> None:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        tmp.write("not valid json{{{")
        tmp.close()
        path = Path(tmp.name)
        try:
            client = LocalDataRetriever(data_path=path)
            self.assertTrue(client.available())  # file exists...
            self.assertIsNone(client.retrieve("cardiology", None))  # ...but unreadable -> None
        finally:
            path.unlink()

    def test_top_level_non_list_json_returns_none(self) -> None:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"not": "a list"}, tmp)
        tmp.close()
        path = Path(tmp.name)
        try:
            client = LocalDataRetriever(data_path=path)
            self.assertIsNone(client.retrieve("cardiology", None))
        finally:
            path.unlink()

    def test_failed_load_is_not_retried_every_call(self) -> None:
        client = LocalDataRetriever(data_path="/nonexistent/path/facilities.json")

        client.retrieve("cardiology", None)
        client.retrieve("cardiology", None)

        self.assertTrue(client._load_attempted)
        self.assertIsNone(client._rows)


if __name__ == "__main__":
    unittest.main()
