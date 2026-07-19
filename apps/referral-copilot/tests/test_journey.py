"""Contracts for Aven's no-key journey and ambulance action layer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.journey import (  # noqa: E402
    build_ambulance_plan,
    demo_journey_estimate,
    external_ticket_links,
    google_maps_directions_url,
)


class GoogleMapsUrlTests(unittest.TestCase):
    def test_directions_url_needs_no_key_and_encodes_the_route(self) -> None:
        url = google_maps_directions_url(
            "Boring Road, Patna", "Demo District Care Centre", "motorbike"
        )
        self.assertTrue(url.startswith("https://www.google.com/maps/dir/?api=1&"))
        self.assertIn("origin=Boring+Road%2C+Patna", url)
        self.assertIn("destination=Demo+District+Care+Centre", url)
        self.assertIn("travelmode=two-wheeler", url)
        self.assertNotIn("key=", url)

    def test_blank_origin_or_destination_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            google_maps_directions_url("", "Hospital", "car")


class DemoEstimateTests(unittest.TestCase):
    def test_seeded_estimate_is_explicit_and_bounded(self) -> None:
        estimate = demo_journey_estimate(18, "bus")
        self.assertGreater(estimate.duration_minutes, 0)
        self.assertGreaterEqual(estimate.cost_high_rupees, estimate.cost_low_rupees)
        self.assertTrue(estimate.is_seeded_demo)
        self.assertIn("not a live", estimate.disclaimer.casefold())

    def test_ambulance_estimate_never_claims_free_service(self) -> None:
        estimate = demo_journey_estimate(18, "ambulance")
        self.assertGreater(estimate.cost_low_rupees, 0)
        self.assertIn("may be free", estimate.disclaimer.casefold())


class AmbulancePlanTests(unittest.TestCase):
    def test_documented_service_with_verified_phone_can_be_called(self) -> None:
        plan = build_ambulance_plan(
            distance_km=12,
            service_documented=True,
            verified_hospital_phone="+91 612 234 5678",
            selected=True,
        )
        self.assertEqual(plan.service_status, "documented")
        self.assertEqual(plan.call_url, "tel:+916122345678")
        self.assertFalse(plan.phone_needs_verification)
        self.assertIsNotNone(plan.estimate)

    def test_tavily_phone_is_a_candidate_and_must_be_verified(self) -> None:
        plan = build_ambulance_plan(
            distance_km=12,
            service_documented=False,
            candidate_phones=("0612-2345678",),
            selected=True,
        )
        self.assertEqual(plan.service_status, "not_documented")
        self.assertEqual(plan.call_url, "tel:06122345678")
        self.assertTrue(plan.phone_needs_verification)
        self.assertIn("verify", plan.instruction.casefold())

    def test_missing_phone_never_invents_one_and_exposes_112_for_emergencies(self) -> None:
        plan = build_ambulance_plan(
            distance_km=12,
            service_documented=False,
            selected=True,
        )
        self.assertIsNone(plan.hospital_phone)
        self.assertIsNone(plan.call_url)
        self.assertEqual(plan.emergency_call_url, "tel:112")
        self.assertIn("hospital", plan.instruction.casefold())


class TicketLinkTests(unittest.TestCase):
    def test_only_allowlisted_external_booking_sites_are_returned(self) -> None:
        plane = external_ticket_links("plane")
        train = external_ticket_links("train")
        self.assertEqual([link.label for link in plane], ["Air India", "IndiGo"])
        self.assertTrue(all(link.url.startswith("https://") for link in plane))
        self.assertEqual(train[0].label, "IRCTC")
        self.assertTrue(all(link.external_booking for link in plane + train))


if __name__ == "__main__":
    unittest.main()
