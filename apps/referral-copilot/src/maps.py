"""Provider selection and truth labels for Aven travel comparisons.

This module performs no network I/O.  It validates a future route request and
describes what the configured provider can support so the UI cannot present a
seeded comparison as a live route, fare, or transit update.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


SUPPORTED_TRAVEL_MODES = (
    "walk",
    "bicycle",
    "motorbike",
    "car",
    "bus",
    "train",
    "taxi",
    "plane",
)

_GOOGLE_ROUTE_MODES = {
    "walk": "WALK",
    "bicycle": "BICYCLE",
    "motorbike": "TWO_WHEELER",
    "car": "DRIVE",
    "bus": "TRANSIT",
    "train": "TRANSIT",
}
_ORS_ROUTE_MODES = {"walk": "foot-walking", "bicycle": "cycling-regular", "car": "driving-car"}
_GOOGLE_BETA_MODES = frozenset({"walk", "bicycle", "motorbike"})


@dataclass(frozen=True)
class MapProvider:
    """Selected routing provider without retaining or exposing its secret."""

    name: str
    credential_env_var: str | None
    is_live_provider: bool


@dataclass(frozen=True)
class TravelModeCapability:
    """Honest, user-visible capability labels for one provider and mode."""

    mode: str
    provider_mode: str | None
    route_supported: bool
    comparison_only: bool
    live_price_supported: bool
    live_transit_supported: bool
    user_label: str


@dataclass(frozen=True)
class RouteRequest:
    """Validated route intent; result fields remain unknown until an adapter runs."""

    provider: MapProvider
    origin: tuple[float, float]
    destination: tuple[float, float]
    mode: str
    capability: TravelModeCapability
    distance_km: float | None = None
    duration_minutes: float | None = None
    price: float | None = None


def _configured(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold()
    if not normalized:
        return False
    return not normalized.startswith(("todo", "replace_me", "your_"))


def select_map_provider(env: Mapping[str, str] | None = None) -> MapProvider:
    """Choose Google, then ORS, then the deterministic offline demo fallback.

    Only the credential's environment-variable name is returned.  Secret
    values never enter the configuration object, logs, or its representation.
    """

    configured_env = os.environ if env is None else env
    if _configured(configured_env.get("GOOGLE_MAPS_API_KEY")):
        return MapProvider("google", "GOOGLE_MAPS_API_KEY", True)
    if _configured(configured_env.get("OPENROUTESERVICE_API_KEY")):
        return MapProvider("openrouteservice", "OPENROUTESERVICE_API_KEY", True)
    return MapProvider("demo", None, False)


def validate_travel_mode(mode: str) -> str:
    """Normalize a supported product mode or reject it without guessing."""

    if not isinstance(mode, str):
        raise ValueError("Travel mode must be one of Aven's supported modes.")
    normalized = mode.strip().casefold()
    if normalized not in SUPPORTED_TRAVEL_MODES:
        raise ValueError(
            "Unsupported travel mode. Choose walk, bicycle, motorbike, car, bus, train, taxi, or plane."
        )
    return normalized


def validate_coordinates(coordinates: Sequence[object]) -> tuple[float, float]:
    """Validate a `(latitude, longitude)` pair and return finite floats."""

    if isinstance(coordinates, (str, bytes)) or not isinstance(coordinates, Sequence):
        raise ValueError("Coordinates must contain latitude and longitude.")
    if len(coordinates) != 2:
        raise ValueError("Coordinates must contain exactly latitude and longitude.")

    latitude, longitude = coordinates
    if (
        isinstance(latitude, bool)
        or isinstance(longitude, bool)
        or not isinstance(latitude, (int, float))
        or not isinstance(longitude, (int, float))
    ):
        raise ValueError("Latitude and longitude must be numbers.")

    parsed_latitude = float(latitude)
    parsed_longitude = float(longitude)
    if not math.isfinite(parsed_latitude) or not math.isfinite(parsed_longitude):
        raise ValueError("Latitude and longitude must be finite numbers.")
    if not -90 <= parsed_latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not -180 <= parsed_longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees.")
    return parsed_latitude, parsed_longitude


def mode_capability(provider: MapProvider, mode: str) -> TravelModeCapability:
    """Return route and comparison truth labels for a validated travel mode."""

    normalized_mode = validate_travel_mode(mode)
    if provider.name == "google":
        provider_mode = _GOOGLE_ROUTE_MODES.get(normalized_mode)
        route_supported = provider_mode is not None
        provider_label = "Google"
    elif provider.name == "openrouteservice":
        provider_mode = _ORS_ROUTE_MODES.get(normalized_mode)
        route_supported = provider_mode is not None
        provider_label = "openrouteservice"
    else:
        provider_mode = None
        route_supported = False
        provider_label = "Demo"

    if route_supported:
        user_label = (
            f"{provider_label} route supported for {normalized_mode}; "
            "live price is not provided and live transit status is not confirmed."
        )
        if provider.name == "google" and normalized_mode in _GOOGLE_BETA_MODES:
            user_label += " Google labels this route mode beta; paths may be incomplete."
    else:
        user_label = (
            f"{provider_label} comparison only for {normalized_mode}; "
            "route, live price, and live transit are not provided."
        )

    return TravelModeCapability(
        mode=normalized_mode,
        provider_mode=provider_mode,
        route_supported=route_supported,
        comparison_only=not route_supported,
        live_price_supported=False,
        live_transit_supported=False,
        user_label=user_label,
    )


def build_route_request(
    origin: Sequence[object],
    destination: Sequence[object],
    mode: str,
    *,
    env: Mapping[str, str] | None = None,
) -> RouteRequest:
    """Build a validated provider request without making a network call."""

    provider = select_map_provider(env)
    normalized_mode = validate_travel_mode(mode)
    return RouteRequest(
        provider=provider,
        origin=validate_coordinates(origin),
        destination=validate_coordinates(destination),
        mode=normalized_mode,
        capability=mode_capability(provider, normalized_mode),
    )
