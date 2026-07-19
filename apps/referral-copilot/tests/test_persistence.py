"""Security contracts for owner-scoped Lakebase plan persistence."""

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
    """Stateful fake that applies owner isolation like the target SQL schema."""

    def __init__(self) -> None:
        self.plans: dict[tuple[str, str], str] = {}
        self.feedback: list[tuple[str, str, str]] = []
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, statement: str, parameters: tuple[object, ...]):
        self.calls.append((statement, parameters))
        normalised = " ".join(statement.split()).casefold()
        if normalised.startswith("insert into") and "access_feedback" in normalised:
            owner_id, plan_id, payload, lookup_owner, lookup_plan = map(str, parameters)
            if (lookup_owner, lookup_plan) not in self.plans:
                return []
            self.feedback.append((owner_id, plan_id, payload))
            return [{"feedback_id": len(self.feedback)}]
        if normalised.startswith("insert into") and "saved_care_plans" in normalised:
            owner_id, plan_id, payload = map(str, parameters)
            self.plans[(owner_id, plan_id)] = payload
            return []
        if normalised.startswith("select payload") and "order by updated_at" in normalised:
            owner_id = str(parameters[0])
            return [
                {"payload": payload}
                for (row_owner, _), payload in self.plans.items()
                if row_owner == owner_id
            ]
        if normalised.startswith("select payload"):
            owner_id, plan_id = map(str, parameters)
            payload = self.plans.get((owner_id, plan_id))
            return [] if payload is None else [{"payload": payload}]
        if normalised.startswith("select feedback_payload"):
            owner_id, plan_id = map(str, parameters)
            return [
                {"feedback_payload": payload}
                for row_owner, row_plan, payload in self.feedback
                if (row_owner, row_plan) == (owner_id, plan_id)
            ]
        if normalised.startswith("delete from") and "where owner_id" in normalised:
            owner_id, plan_id = map(str, parameters)
            existed = self.plans.pop((owner_id, plan_id), None) is not None
            if existed:
                self.feedback = [
                    row for row in self.feedback if row[:2] != (owner_id, plan_id)
                ]
            return [{"plan_id": plan_id}] if existed else []
        if normalised.startswith("delete from") and "expires_at" in normalised:
            return [{"deleted_count": 0}]
        raise AssertionError(f"Unexpected SQL: {statement}")


class PersistentPlanStoreTests(unittest.TestCase):
    def test_lists_only_the_signed_in_owners_unexpired_plans(self) -> None:
        database = InMemoryPostgresExecutor()
        owner_a = PersistentSqlPlanStore(database, owner_id="owner-a")
        owner_b = PersistentSqlPlanStore(database, owner_id="owner-b")
        owner_a.save_plan({"plan_id": "a-1", "selected_facility_id": "facility-a"})
        owner_b.save_plan({"plan_id": "b-1", "selected_facility_id": "facility-b"})

        self.assertEqual(owner_a.list_plans()[0]["plan_id"], "a-1")
        self.assertNotIn("facility-b", repr(owner_a.list_plans()))

    def test_plan_survives_new_store_instance_for_same_owner(self) -> None:
        database = InMemoryPostgresExecutor()
        first = PersistentSqlPlanStore(database, owner_id="owner-a")
        second = PersistentSqlPlanStore(database, owner_id="owner-a")

        first.save_plan({"plan_id": "plan-1", "selected_facility_id": "patna-01"})

        self.assertEqual(
            second.get_plan("plan-1"),
            {"plan_id": "plan-1", "selected_facility_id": "patna-01"},
        )

    def test_owner_cannot_read_or_list_another_owners_records(self) -> None:
        database = InMemoryPostgresExecutor()
        owner_a = PersistentSqlPlanStore(database, owner_id="owner-a")
        owner_b = PersistentSqlPlanStore(database, owner_id="owner-b")
        owner_a.save_plan({"plan_id": "same-id", "selected_facility_id": "a"})
        owner_b.save_plan({"plan_id": "same-id", "selected_facility_id": "b"})
        owner_a.save_feedback("same-id", {"status": "helpful", "note": "A"})

        self.assertEqual(owner_a.get_plan("same-id")["selected_facility_id"], "a")
        self.assertEqual(owner_b.get_plan("same-id")["selected_facility_id"], "b")
        self.assertEqual(owner_b.list_feedback("same-id"), ())
        for statement, parameters in database.calls:
            if "plan_id" in statement.casefold():
                self.assertIn(parameters[0], ("owner-a", "owner-b"))

    def test_user_values_are_bound_parameters_not_sql_text(self) -> None:
        database = InMemoryPostgresExecutor()
        store = PersistentSqlPlanStore(database, owner_id="owner-a")
        user_value = "note'); DROP TABLE saved_care_plans; --"

        store.save_plan(
            {
                "plan_id": "plan-2",
                "user_override": {"note": user_value, "facility_id": "f-1"},
            }
        )

        statement, parameters = database.calls[0]
        self.assertNotIn(user_value, statement)
        self.assertEqual(statement.count("%s"), 3)
        self.assertIn(user_value, json.loads(str(parameters[2]))["user_override"]["note"])

    def test_sensitive_intake_is_not_persisted_with_the_saved_decision(self) -> None:
        store = PersistentSqlPlanStore(InMemoryPostgresExecutor(), owner_id="owner-a")

        saved = store.save_plan(
            {
                "plan_id": "plan-minimal",
                "demo_user_id": "mariam@example.com",
                "confirmed_request": {
                    "original_text": "I need my metformin refilled",
                    "medication_name": "metformin",
                    "location": "home address",
                },
                "selected_facility_id": "pharmacy-1",
                "selected_option": {
                    "facility": "Demo Pharmacy",
                    "transcript": "Please refill metformin",
                    "metadata": {"email": "mariam@example.com", "evidence": "row-1"},
                },
                "next_steps": ["Call to confirm"],
            }
        )

        self.assertEqual(
            saved,
            {
                "plan_id": "plan-minimal",
                "selected_facility_id": "pharmacy-1",
                "selected_option": {
                    "facility": "Demo Pharmacy",
                    "metadata": {"evidence": "row-1"},
                },
                "next_steps": ["Call to confirm"],
            },
        )

    def test_feedback_is_bounded_append_only_and_requires_owned_plan(self) -> None:
        database = InMemoryPostgresExecutor()
        store = PersistentSqlPlanStore(database, owner_id="owner-a")
        store.save_plan({"plan_id": "plan-3", "selected_facility_id": "f-1"})

        store.save_feedback("plan-3", {"status": "helpful", "note": "Useful"})
        store.save_feedback("plan-3", {"status": "price_differed", "note": "Different"})

        self.assertEqual(
            store.list_feedback("plan-3"),
            (
                {"plan_id": "plan-3", "status": "helpful", "note": "Useful"},
                {"plan_id": "plan-3", "status": "price_differed", "note": "Different"},
            ),
        )
        with self.assertRaises(KeyError):
            store.save_feedback("unknown-plan", {"status": "helpful"})
        with self.assertRaises(ValueError):
            store.save_feedback("plan-3", {"status": "arbitrary-status"})

    def test_owner_can_delete_own_plan_and_feedback_only(self) -> None:
        database = InMemoryPostgresExecutor()
        owner_a = PersistentSqlPlanStore(database, owner_id="owner-a")
        owner_b = PersistentSqlPlanStore(database, owner_id="owner-b")
        owner_a.save_plan({"plan_id": "shared-name", "selected_facility_id": "a"})
        owner_b.save_plan({"plan_id": "shared-name", "selected_facility_id": "b"})
        owner_a.save_feedback("shared-name", {"status": "helpful"})

        self.assertTrue(owner_a.delete_plan("shared-name"))
        self.assertIsNone(owner_a.get_plan("shared-name"))
        self.assertEqual(owner_a.list_feedback("shared-name"), ())
        self.assertIsNotNone(owner_b.get_plan("shared-name"))

    def test_identifiers_lengths_and_payloads_are_validated_before_sql(self) -> None:
        database = InMemoryPostgresExecutor()
        with self.assertRaises(ValueError):
            PersistentSqlPlanStore(database, owner_id="")
        with self.assertRaises(ValueError):
            PersistentSqlPlanStore(
                database,
                owner_id="owner-a",
                plans_table="saved_care_plans; DROP TABLE users",
            )

        store = PersistentSqlPlanStore(database, owner_id="owner-a")
        for invalid_plan_id in ("", "spaces are unsafe", "x" * 129):
            with self.subTest(plan_id=invalid_plan_id):
                with self.assertRaises(ValueError):
                    store.save_plan({"plan_id": invalid_plan_id})
        with self.assertRaises(ValueError):
            store.save_plan({"plan_id": "plan-large", "next_steps": ["x" * 70_000]})
        self.assertEqual(database.calls, [])

        valid = PersistentSqlPlanStore(
            database,
            owner_id="owner-a",
            plans_table="aven.saved_care_plans",
            feedback_table="aven.access_feedback",
        )
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9_.]+", valid.plans_table))


if __name__ == "__main__":
    unittest.main()
