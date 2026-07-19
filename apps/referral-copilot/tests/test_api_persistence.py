"""End-to-end API checks for minimized saved decisions in local-demo mode."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.api import app  # noqa: E402
from src.backend.lakebase import _LOCAL_SESSIONS  # noqa: E402


class ApiPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        _LOCAL_SESSIONS.clear()
        self.environment = patch.dict(
            os.environ,
            {"AVEN_AUTH_MODE": "local_demo", "AVEN_ALLOW_LOCAL_DEMO": "true"},
            clear=False,
        )
        self.environment.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.environment.stop()
        _LOCAL_SESSIONS.clear()

    def test_save_reload_feedback_and_delete_without_health_intake(self) -> None:
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("aven", page.text.casefold())

        response = self.client.post(
            "/api/plans",
            json={
                "plan_id": "api-plan-1",
                "selected_facility_id": "facility-1",
                "selected_option": {
                    "facility_id": "facility-1",
                    "display_name": "Demo hospital",
                    "reason": "Documented capability",
                },
                "next_steps": ["Call to confirm"],
                "user_override": {"note": "Ask about step-free access"},
                # Unknown fields are ignored by the request model and must never
                # reach persistence.
                "confirmed_request": {"location": "Private home address"},
                "medication_name": "Sensitive medicine",
                "transcript": "Sensitive spoken intake",
            },
        )
        self.assertEqual(response.status_code, 200)
        saved = response.json()["plan"]
        self.assertEqual(response.json()["persistence"], "local_demo")
        self.assertNotIn("confirmed_request", saved)
        self.assertNotIn("medication_name", saved)
        self.assertNotIn("transcript", saved)

        listed = self.client.get("/api/plans")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([row["plan_id"] for row in listed.json()["plans"]], ["api-plan-1"])

        feedback = self.client.post(
            "/api/plans/api-plan-1/feedback",
            json={"status": "helpful", "note": "Route made sense"},
        )
        self.assertEqual(feedback.status_code, 200)

        deleted = self.client.delete("/api/plans/api-plan-1")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["deleted"])
        self.assertEqual(self.client.get("/api/plans").json()["plans"], [])

    def test_two_demo_visitors_do_not_share_saved_plans(self) -> None:
        """A public demo host must not leak one visitor's plans to another.

        Each client keeps its own cookie jar, so this exercises two separate
        browser sessions against the same process.
        """

        plan = {
            "plan_id": "shared-test-plan",
            "selected_facility_id": "facility-1",
            "selected_option": {"facility_id": "facility-1", "display_name": "Demo hospital"},
            "next_steps": [],
        }

        with TestClient(app) as visitor_a, TestClient(app) as visitor_b:
            self.assertEqual(visitor_a.post("/api/plans", json=plan).status_code, 200)
            self.assertEqual(
                [row["plan_id"] for row in visitor_a.get("/api/plans").json()["plans"]],
                ["shared-test-plan"],
            )

            # B has saved nothing and must not observe A's plan.
            self.assertEqual(visitor_b.get("/api/plans").json()["plans"], [])

            # The same plan ID for B stays a distinct record.
            self.assertEqual(visitor_b.post("/api/plans", json=plan).status_code, 200)
            self.assertEqual(len(visitor_a.get("/api/plans").json()["plans"]), 1)

            # Deleting B's copy must leave A's intact.
            self.assertTrue(visitor_b.delete("/api/plans/shared-test-plan").json()["deleted"])
            self.assertEqual(
                [row["plan_id"] for row in visitor_a.get("/api/plans").json()["plans"]],
                ["shared-test-plan"],
            )


if __name__ == "__main__":
    unittest.main()
