"""Contract tests for Aven's provider-aware travel planning adapter."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.maps import (  # noqa: E402
    SUPPORTED_TRAVEL_MODES,
    build_route_request,
    mode_capability,
    select_map_provider,
    validate_coordinates,
    validate_travel_mode,
)


class ProviderSelectionTests(unittest.TestCase):
    def test_google_is_selected_when_its_key_is_configured(self) -> None:
        provider = select_map_provider(
            {
                "GOOGLE_MAPS_API_KEY": "google-secret",
                "OPENROUTESERVICE_API_KEY": "ors-secret",
            }
        )

        self.assertEqual(provider.name, "google")
        self.assertEqual(provider.credential_env_var, "GOOGLE_MAPS_API_KEY")
        self.assertTrue(provider.is_live_provider)
        self.assertNotIn("google-secret", repr(provider))

    def test_ors_is_selected_when_google_is_not_configured(self) -> None:
        provider = select_map_provider(
            {"GOOGLE_MAPS_API_KEY": "  ", "OPENROUTESERVICE_API_KEY": "ors-secret"}
        )

        self.assertEqual(provider.name, "openrouteservice")
        self.assertEqual(provider.credential_env_var, "OPENROUTESERVICE_API_KEY")
        self.assertTrue(provider.is_live_provider)

    def test_offline_demo_is_the_safe_default(self) -> None:
        provider = select_map_provider({})

        self.assertEqual(provider.name, "demo")
        self.assertIsNone(provider.credential_env_var)
        self.assertFalse(provider.is_live_provider)


class ValidationTests(unittest.TestCase):
    def test_all_and_only_product_modes_are_whitelisted(self) -> None:
        self.assertEqual(
            SUPPORTED_TRAVEL_MODES,
            ("walk", "cycle", "motorbike", "car", "taxi", "bus", "train", "plane"),
        )

    def test_travel_mode_is_normalized_and_invalid_modes_are_rejected(self) -> None:
        self.assertEqual(validate_travel_mode(" Walk "), "walk")
        for invalid in ("", "ambulance", "spaceship", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_travel_mode(invalid)  # type: ignore[arg-type]

    def test_coordinate_boundaries_are_accepted(self) -> None:
        self.assertEqual(validate_coordinates((90, -180)), (90.0, -180.0))
        self.assertEqual(validate_coordinates((-90, 180)), (-90.0, 180.0))

    def test_invalid_coordinates_are_rejected(self) -> None:
        invalid_coordinates = (
            (90.01, 0),
            (0, -180.01),
            (math.nan, 0),
            (True, 1),
            ("Patna", 85.1),
            (25.6,),
        )
        for coordinates in invalid_coordinates:
            with self.subTest(coordinates=coordinates):
                with self.assertRaises(ValueError):
                    validate_coordinates(coordinates)  # type: ignore[arg-type]


class CapabilityTruthLabelTests(unittest.TestCase):
    def test_google_supports_routes_but_never_claims_live_prices(self) -> None:
        google = select_map_provider({"GOOGLE_MAPS_API_KEY": "configured"})

        for mode in ("walk", "cycle", "motorbike", "car", "bus", "train"):
            with self.subTest(mode=mode):
                capability = mode_capability(google, mode)
                self.assertTrue(capability.route_supported)
                self.assertFalse(capability.comparison_only)
                self.assertFalse(capability.live_price_supported)

        for mode in ("taxi", "plane"):
            with self.subTest(mode=mode):
                capability = mode_capability(google, mode)
                self.assertFalse(capability.route_supported)
                self.assertTrue(capability.comparison_only)
                self.assertFalse(capability.live_price_supported)

    def test_transit_is_never_labelled_live_by_capability_alone(self) -> None:
        google = select_map_provider({"GOOGLE_MAPS_API_KEY": "configured"})

        for mode in SUPPORTED_TRAVEL_MODES:
            with self.subTest(mode=mode):
                self.assertFalse(mode_capability(google, mode).live_transit_supported)

    def test_ors_supports_only_its_explicit_route_profiles(self) -> None:
        ors = select_map_provider({"OPENROUTESERVICE_API_KEY": "configured"})

        for mode in ("walk", "cycle", "car"):
            with self.subTest(mode=mode):
                self.assertTrue(mode_capability(ors, mode).route_supported)

        for mode in ("motorbike", "taxi", "bus", "train", "plane"):
            with self.subTest(mode=mode):
                capability = mode_capability(ors, mode)
                self.assertFalse(capability.route_supported)
                self.assertTrue(capability.comparison_only)
                self.assertFalse(capability.live_price_supported)
                self.assertFalse(capability.live_transit_supported)

    def test_offline_demo_never_presents_seeded_comparisons_as_live_routes(self) -> None:
        demo = select_map_provider({})

        for mode in SUPPORTED_TRAVEL_MODES:
            with self.subTest(mode=mode):
                capability = mode_capability(demo, mode)
                self.assertFalse(capability.route_supported)
                self.assertTrue(capability.comparison_only)
                self.assertFalse(capability.live_price_supported)
                self.assertFalse(capability.live_transit_supported)
                self.assertIn("demo", capability.user_label.casefold())

    def test_route_request_contains_validated_truth_labels_without_network_io(self) -> None:
        request = build_route_request(
            (25.5941, 85.1376),
            (25.611, 85.144),
            "car",
            env={"OPENROUTESERVICE_API_KEY": "configured"},
        )

        self.assertEqual(request.provider.name, "openrouteservice")
        self.assertEqual(request.mode, "car")
        self.assertEqual(request.origin, (25.5941, 85.1376))
        self.assertTrue(request.capability.route_supported)
        self.assertIsNone(request.distance_km)
        self.assertIsNone(request.duration_minutes)
        self.assertIsNone(request.price)


if __name__ == "__main__":
    unittest.main()
