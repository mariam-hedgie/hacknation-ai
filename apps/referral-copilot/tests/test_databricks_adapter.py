"""Contract tests for Aven's Databricks boundary and state fallback."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.databricks_adapter import (  # noqa: E402
    ConfigurationError,
    DatabricksConfig,
    DatabricksFacilityRepository,
    FallbackPlanStore,
    SessionLocalPlanStore,
    load_databricks_config,
)
from src.domain import EvidenceStatus  # noqa: E402


class RecordingExecutor:
    def __init__(self, rows: list[dict[str, object]] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, statement: str, parameters: tuple[object, ...]) -> list[dict[str, object]]:
        self.calls.append((statement, parameters))
        return self.rows


class FailingPlanStore:
    def save_plan(self, plan: dict[str, object]) -> dict[str, object]:
        raise ConnectionError("database unavailable")

    def get_plan(self, plan_id: str) -> dict[str, object] | None:
        raise ConnectionError("database unavailable")

    def save_feedback(self, plan_id: str, feedback: dict[str, object]) -> dict[str, object]:
        raise ConnectionError("database unavailable")

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]:
        raise ConnectionError("database unavailable")


class DatabricksConfigTests(unittest.TestCase):
    def test_config_requires_hostname_and_http_path_without_a_token(self) -> None:
        config = DatabricksConfig.from_env(
            {
                "DATABRICKS_SERVER_HOSTNAME": "dbc.example.cloud.databricks.com",
                "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/demo",
                "DATABRICKS_TOKEN": "must-not-be-read",
            }
        )

        self.assertEqual(config.server_hostname, "dbc.example.cloud.databricks.com")
        self.assertEqual(config.http_path, "/sql/1.0/warehouses/demo")
        self.assertNotIn("token", repr(config).casefold())
        self.assertEqual(set(config.__dataclass_fields__), {"server_hostname", "http_path"})

    def test_config_error_names_missing_variables_but_never_values(self) -> None:
        with self.assertRaises(ConfigurationError) as context:
            DatabricksConfig.from_env(
                {
                    "DATABRICKS_SERVER_HOSTNAME": "",
                    "DATABRICKS_HTTP_PATH": "",
                    "DATABRICKS_TOKEN": "sensitive-token-value",
                }
            )

        message = str(context.exception)
        self.assertIn("DATABRICKS_SERVER_HOSTNAME", message)
        self.assertIn("DATABRICKS_HTTP_PATH", message)
        self.assertNotIn("sensitive-token-value", message)

    def test_optional_loader_returns_none_for_safe_disconnected_mode(self) -> None:
        self.assertIsNone(load_databricks_config({}))


class FacilityRepositoryTests(unittest.TestCase):
    def test_disconnected_repository_returns_an_explicit_empty_result(self) -> None:
        result = DatabricksFacilityRepository().find_by_capability("cardiology")

        self.assertFalse(result.connected)
        self.assertEqual(result.candidates, ())
        self.assertIn("not configured", result.message.casefold())

    def test_query_uses_placeholders_and_keeps_user_input_out_of_sql(self) -> None:
        executor = RecordingExecutor()
        repository = DatabricksFacilityRepository(executor)
        user_input = "cardiology' OR 1=1 --"

        repository.find_by_capability(user_input, limit=7)

        statement, parameters = executor.calls[0]
        self.assertNotIn(user_input, statement)
        self.assertIn("e.capability = ?", statement)
        self.assertIn("LIMIT ?", statement)
        self.assertEqual(parameters, (user_input, 7))

    def test_row_translation_preserves_evidence_missing_fields_and_source_span(self) -> None:
        executor = RecordingExecutor(
            [
                {
                    "facility_id": "patna-01",
                    "display_name": "Patna Demo Hospital",
                    "capability": "cardiology",
                    "data_status": "documented",
                    "contradiction_flag": False,
                    "distance_km": 4.25,
                    "facility_type": "public",
                    "missing_fields": '["consultation_fee", "appointment_url"]',
                    "literal_source_text": "Services include cardiology and general medicine.",
                    "cited_span": "cardiology",
                    "source_column": "services",
                    "source_row_id": "row-88",
                }
            ]
        )

        result = DatabricksFacilityRepository(executor).find_by_capability("cardiology")

        candidate = result.candidates[0]
        self.assertTrue(result.connected)
        self.assertEqual(candidate.facility_id, "patna-01")
        self.assertEqual(candidate.evidence_status, EvidenceStatus.DOCUMENTED)
        self.assertEqual(candidate.missing_fields, ("consultation_fee", "appointment_url"))
        self.assertEqual(candidate.source_spans, ("services [row-88]: cardiology",))

    def test_unsupported_or_missing_literal_span_is_not_documented(self) -> None:
        executor = RecordingExecutor(
            [
                {
                    "facility_id": "facility-02",
                    "display_name": "Unverified Facility",
                    "capability": "cardiology",
                    "data_status": "documented",
                    "literal_source_text": "General outpatient care only.",
                    "cited_span": "cardiology",
                    "source_column": "services",
                    "source_row_id": "row-2",
                    "missing_fields": (),
                }
            ]
        )

        candidate = DatabricksFacilityRepository(executor).find_by_capability(
            "cardiology"
        ).candidates[0]

        self.assertEqual(candidate.evidence_status, EvidenceStatus.NOT_DOCUMENTED)
        self.assertIn("evidence_span", candidate.missing_fields)
        self.assertEqual(candidate.source_spans, ())

    def test_contradiction_takes_priority_over_a_literal_documented_span(self) -> None:
        executor = RecordingExecutor(
            [
                {
                    "facility_id": "facility-03",
                    "display_name": "Conflicting Facility",
                    "capability": "cardiology",
                    "data_status": "documented",
                    "contradiction_flag": True,
                    "literal_source_text": "Cardiology is listed in the source.",
                    "cited_span": "Cardiology",
                    "source_column": "services",
                    "source_row_id": "row-3",
                    "missing_fields": "consultation_fee, current_availability",
                }
            ]
        )

        candidate = DatabricksFacilityRepository(executor).find_by_capability(
            "cardiology"
        ).candidates[0]

        self.assertEqual(candidate.evidence_status, EvidenceStatus.CONFLICTING)
        self.assertEqual(
            candidate.missing_fields, ("consultation_fee", "current_availability")
        )


class SessionPersistenceTests(unittest.TestCase):
    def test_session_store_persists_across_instances_sharing_session_state(self) -> None:
        session_state: dict[str, object] = {}
        first = SessionLocalPlanStore(session_state)
        second = SessionLocalPlanStore(session_state)

        saved = first.save_plan(
            {
                "plan_id": "plan-1",
                "demo_user_id": "demo-user",
                "selected_facility_id": "patna-01",
            }
        )
        reopened = second.get_plan("plan-1")

        self.assertEqual(saved, reopened)
        self.assertIsNot(saved, reopened)

    def test_plan_requires_a_nonempty_plan_id(self) -> None:
        store = SessionLocalPlanStore({})

        with self.assertRaises(ValueError):
            store.save_plan({"plan_id": ""})

    def test_feedback_is_append_only_and_returned_as_copies(self) -> None:
        store = SessionLocalPlanStore({})
        original = {"status": "price_differed", "note": "Call quoted another fee"}

        stored = store.save_feedback("plan-1", original)
        original["note"] = "mutated later"
        feedback = store.list_feedback("plan-1")

        self.assertEqual(stored["note"], "Call quoted another fee")
        self.assertEqual(feedback[0]["note"], "Call quoted another fee")
        self.assertIsNot(stored, feedback[0])

    def test_primary_failure_falls_back_without_losing_the_plan(self) -> None:
        fallback = SessionLocalPlanStore({})
        store = FallbackPlanStore(FailingPlanStore(), fallback)

        saved = store.save_plan({"plan_id": "plan-fallback", "care_task": "lab"})

        self.assertEqual(saved["plan_id"], "plan-fallback")
        self.assertEqual(store.get_plan("plan-fallback"), saved)
        self.assertTrue(store.using_fallback)


if __name__ == "__main__":
    unittest.main()
