"""Runtime wiring contracts for managed Lakebase OAuth persistence."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.lakebase import LakebasePostgresExecutor  # noqa: E402


class FakeCursor:
    description = (("plan_id",),)

    def __init__(self) -> None:
        self.statement = ""
        self.parameters: tuple[object, ...] = ()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, statement: str, parameters: tuple[object, ...]) -> None:
        self.statement = statement
        self.parameters = parameters

    def fetchall(self):
        return [("plan-1",)]


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def cursor(self):
        return self.cursor_instance


class LakebaseRuntimeTests(unittest.TestCase):
    def test_requires_every_managed_resource_coordinate(self) -> None:
        with self.assertRaises(RuntimeError):
            LakebasePostgresExecutor(environ={})

    def test_generates_a_fresh_oauth_credential_and_binds_user_values(self) -> None:
        connection = FakeConnection()
        calls: list[dict[str, object]] = []

        def connect(**kwargs):
            calls.append(kwargs)
            return connection

        executor = LakebasePostgresExecutor(
            environ={
                "PGHOST": "database.example",
                "PGDATABASE": "databricks_postgres",
                "PGUSER": "service-principal-id",
                "PGPORT": "5432",
                "PGSSLMODE": "require",
                "ENDPOINT_NAME": "projects/p/branches/b/endpoints/e",
            },
            credential_provider=lambda endpoint: f"short-lived:{endpoint}",
            connect=connect,
        )

        rows = executor.execute("SELECT %s AS plan_id", ("plan-1",))

        self.assertEqual(rows, ({"plan_id": "plan-1"},))
        self.assertEqual(connection.cursor_instance.parameters, ("plan-1",))
        self.assertNotIn("plan-1", connection.cursor_instance.statement)
        self.assertEqual(calls[0]["password"], "short-lived:projects/p/branches/b/endpoints/e")
        self.assertEqual(calls[0]["sslmode"], "require")


if __name__ == "__main__":
    unittest.main()
