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
from src.backend.lakebase import _LOCAL_STATE  # noqa: E402


class ApiPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        _LOCAL_STATE.clear()
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
        _LOCAL_STATE.clear()

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

    def test_unverified_facility_name_opens_a_maps_search_not_directions(self) -> None:
        response = self.client.post(
            "/api/journey",
            json={
                "origin": "Mumbai, Maharashtra",
                "destination": "City Heart Centre",
                "mode": "car",
                "distance_km": None,
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["destination_needs_confirmation"])
        self.assertTrue(result["maps_url"].startswith("https://www.google.com/maps/search/?api=1&"))
        self.assertNotIn("/maps/dir/", result["maps_url"])
        self.assertEqual(self.client.get("/api/plans").json()["plans"], [])


if __name__ == "__main__":
    unittest.main()
