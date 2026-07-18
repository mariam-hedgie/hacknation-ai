"""Contract tests for durable Lakebase-compatible plan persistence."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.persistence import PersistentSqlPlanStore  # noqa: E402


class InMemoryPostgresExecutor:
    """Tiny stateful fake that verifies the adapter's bound-parameter contract."""

    def __init__(self) -> None:
        self.plans: dict[str, str] = {}
        self.feedback: list[tuple[str, str]] = []
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, statement: str, parameters: tuple[object, ...]):
        self.calls.append((statement, parameters))
        normalised = " ".join(statement.split()).casefold()
        if normalised.startswith("insert into") and "saved_care_plans" in normalised:
            plan_id, payload = parameters
            self.plans[str(plan_id)] = str(payload)
            return []
        if normalised.startswith("select payload"):
            payload = self.plans.get(str(parameters[0]))
            return [] if payload is None else [{"payload": payload}]
        if normalised.startswith("insert into") and "access_feedback" in normalised:
            plan_id, payload = parameters
            self.feedback.append((str(plan_id), str(payload)))
            return []
        if normalised.startswith("select feedback_payload"):
            return [
                {"feedback_payload": payload}
                for plan_id, payload in self.feedback
                if plan_id == str(parameters[0])
            ]
        raise AssertionError(f"Unexpected SQL: {statement}")


class PersistentPlanStoreTests(unittest.TestCase):
    def test_plan_survives_new_store_instance_using_same_database(self) -> None:
        database = InMemoryPostgresExecutor()
        first = PersistentSqlPlanStore(database)
        second = PersistentSqlPlanStore(database)

        first.save_plan({"plan_id": "plan-1", "selected_facility_id": "patna-01"})

        self.assertEqual(
            second.get_plan("plan-1"),
            {"plan_id": "plan-1", "selected_facility_id": "patna-01"},
        )

    def test_user_values_are_bound_parameters_not_sql_text(self) -> None:
        database = InMemoryPostgresExecutor()
        store = PersistentSqlPlanStore(database)
        user_value = "note'); DROP TABLE saved_care_plans; --"

        store.save_plan({"plan_id": "plan-2", "note": user_value})

        statement, parameters = database.calls[0]
        self.assertNotIn(user_value, statement)
        self.assertEqual(statement.count("%s"), 2)
        self.assertIn(user_value, json.loads(str(parameters[1]))["note"])

    def test_feedback_is_append_only_and_decoded(self) -> None:
        database = InMemoryPostgresExecutor()
        store = PersistentSqlPlanStore(database)

        store.save_feedback("plan-3", {"status": "call_confirmed"})
        store.save_feedback("plan-3", {"status": "price_differed"})

        self.assertEqual(
            store.list_feedback("plan-3"),
            (
                {"plan_id": "plan-3", "status": "call_confirmed"},
                {"plan_id": "plan-3", "status": "price_differed"},
            ),
        )

    def test_plan_id_is_required(self) -> None:
        store = PersistentSqlPlanStore(InMemoryPostgresExecutor())

        with self.assertRaises(ValueError):
            store.save_plan({"plan_id": ""})

    def test_table_identifiers_are_strictly_validated(self) -> None:
        with self.assertRaises(ValueError):
            PersistentSqlPlanStore(
                InMemoryPostgresExecutor(),
                plans_table="saved_care_plans; DROP TABLE users",
            )

        valid = PersistentSqlPlanStore(
            InMemoryPostgresExecutor(),
            plans_table="aven.saved_care_plans",
            feedback_table="aven.access_feedback",
        )
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9_.]+", valid.plans_table))

    def test_oversized_user_payload_is_rejected_before_database_write(self) -> None:
        database = InMemoryPostgresExecutor()
        store = PersistentSqlPlanStore(database)

        with self.assertRaises(ValueError):
            store.save_plan({"plan_id": "plan-large", "note": "x" * 70_000})

        self.assertEqual(database.calls, [])


if __name__ == "__main__":
    unittest.main()
