"""Safe journey actions for Aven's no-key hackathon experience.

Google Maps URLs open an external route without an API key. Durations and costs
in this module are seeded demo comparisons, never live traffic or fare quotes.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from urllib.parse import urlencode

from .maps import validate_travel_mode


@dataclass(frozen=True)
class JourneyEstimate:
    mode: str
    distance_km: float
    duration_minutes: int
    cost_low_rupees: int
    cost_high_rupees: int
    is_seeded_demo: bool
    disclaimer: str


@dataclass(frozen=True)
class ExternalTicketLink:
    label: str
    url: str
    external_booking: bool = True


@dataclass(frozen=True)
class AmbulancePlan:
    selected: bool
    service_status: str
    hospital_phone: str | None
    call_url: str | None
    phone_needs_verification: bool
    instruction: str
    emergency_call_url: str = "tel:112"
    estimate: JourneyEstimate | None = None


_MAPS_MODES = {
    "walk": "walking",
    "bicycle": "bicycling",
    "motorbike": "two-wheeler",
    "car": "driving",
    "bus": "transit",
    "train": "transit",
    "taxi": "driving",
    "ambulance": "driving",
}

_DEMO_MODE_ASSUMPTIONS = {
    # speed km/h, base cost, per-km low, per-km high
    "walk": (4.5, 0, 0, 0),
    "bicycle": (13.0, 0, 0, 0),
    "motorbike": (28.0, 40, 4, 8),
    "car": (24.0, 100, 8, 15),
    "bus": (20.0, 20, 2, 5),
    "train": (42.0, 80, 2, 7),
    "taxi": (24.0, 120, 12, 22),
    "ambulance": (32.0, 700, 25, 50),
}

_TICKET_LINKS = {
    "bus": (
        ExternalTicketLink("redBus", "https://www.redbus.in/"),
    ),
    "train": (
        ExternalTicketLink("IRCTC", "https://www.irctc.co.in/nget/train-search"),
    ),
    "plane": (
        ExternalTicketLink("Air India", "https://www.airindia.com/"),
        ExternalTicketLink("IndiGo", "https://www.goindigo.in/"),
    ),
}


def _bounded_place(value: object, field: str) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    if not text:
        raise ValueError(f"{field} is required to build a route link.")
    if len(text) > 300:
        raise ValueError(f"{field} is too long to build a route link.")
    return text


def google_maps_directions_url(origin: object, destination: object, mode: str) -> str:
    """Build Google's documented universal Directions URL without a key."""

    normalized_mode = validate_travel_mode(mode)
    params = {
        "api": "1",
        "origin": _bounded_place(origin, "Origin"),
        "destination": _bounded_place(destination, "Destination"),
    }
    maps_mode = _MAPS_MODES.get(normalized_mode)
    if maps_mode:
        params["travelmode"] = maps_mode
    return "https://www.google.com/maps/dir/?" + urlencode(params)


def demo_journey_estimate(distance_km: object, mode: str) -> JourneyEstimate:
    """Return a labelled, deterministic demo comparison from seeded assumptions."""

    normalized_mode = validate_travel_mode(mode)
    if normalized_mode == "plane":
        raise ValueError("Flight duration and fare are deferred to external providers.")
    if isinstance(distance_km, bool) or not isinstance(distance_km, (int, float)):
        raise ValueError("A numeric demo distance is required for an estimate.")
    distance = float(distance_km)
    if not math.isfinite(distance) or distance <= 0 or distance > 5_000:
        raise ValueError("Demo distance must be between 0 and 5,000 km.")
    speed, base, per_km_low, per_km_high = _DEMO_MODE_ASSUMPTIONS[normalized_mode]
    duration = max(5, math.ceil(distance / speed * 60))
    low = round(base + distance * per_km_low)
    high = round(base + distance * per_km_high)
    disclaimer = "Seeded comparison only — not a live route or fare quote."
    if normalized_mode == "ambulance":
        disclaimer += " Hospital or public ambulance service may be free; call to verify service, time, and charge."
    return JourneyEstimate(
        mode=normalized_mode,
        distance_km=distance,
        duration_minutes=duration,
        cost_low_rupees=low,
        cost_high_rupees=high,
        is_seeded_demo=True,
        disclaimer=disclaimer,
    )


def _phone_for_call(value: object) -> tuple[str | None, str | None]:
    display = " ".join(str(value or "").split())
    digits = re.sub(r"\D", "", display)
    if not 8 <= len(digits) <= 15:
        return None, None
    prefix = "+" if display.startswith("+") else ""
    return display, f"tel:{prefix}{digits}"


def build_ambulance_plan(
    *,
    distance_km: float | None,
    service_documented: bool,
    verified_hospital_phone: str | None = None,
    candidate_phones: tuple[str, ...] = (),
    selected: bool,
) -> AmbulancePlan:
    """Create an explicit call/verify action; never infer dispatch or free care."""

    verified_display, verified_url = _phone_for_call(verified_hospital_phone)
    candidate_display: str | None = None
    candidate_url: str | None = None
    for phone in candidate_phones:
        candidate_display, candidate_url = _phone_for_call(phone)
        if candidate_url:
            break

    if verified_url:
        phone = verified_display
        call_url = verified_url
        needs_verification = False
        instruction = "Call the verified hospital number and ask it to confirm ambulance availability, pickup time, and any charge."
    elif candidate_url:
        phone = candidate_display
        call_url = candidate_url
        needs_verification = True
        instruction = "This phone came from a Tavily source candidate. Verify it on the linked page, then call the hospital and confirm ambulance availability, pickup time, and any charge."
    else:
        phone = None
        call_url = None
        needs_verification = True
        instruction = "No verified hospital phone is available yet. Find the hospital's official number, then call and verify ambulance availability, pickup time, and any charge."

    estimate = None
    if selected and distance_km is not None:
        estimate = demo_journey_estimate(distance_km, "ambulance")
    return AmbulancePlan(
        selected=selected,
        service_status="documented" if service_documented else "not_documented",
        hospital_phone=phone,
        call_url=call_url,
        phone_needs_verification=needs_verification,
        instruction=instruction,
        estimate=estimate,
    )


def external_ticket_links(mode: str) -> tuple[ExternalTicketLink, ...]:
    """Return a fixed allowlist; user input can never create an arbitrary URL."""

    return _TICKET_LINKS.get(validate_travel_mode(mode), ())
