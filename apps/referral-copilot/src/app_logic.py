"""Framework-independent orchestration for Aven's confirmed demo journey."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .demo_adapter import build_demo_options
from .domain import IntakeRequest, SafetyBranch, validate_confirmed_intake


@dataclass(frozen=True)
class DemoOutcome:
    """Safe result passed to the UI after confirmation."""

    safety_branch: SafetyBranch
    options: tuple[dict[str, str], ...] = ()
    message: str | None = None
    validation_errors: tuple[str, ...] = ()


def _choice(payload: dict[str, Any], name: str, default: str) -> str:
    value = payload.get(name, default)
    return str(value).strip().casefold() or default


def build_confirmed_request(payload: dict[str, Any]) -> IntakeRequest:
    """Convert reviewed form values into the domain contract.

    This function performs no clinical inference. The UI must show the payload
    to the user before calling it.
    """

    capability = str(payload.get("capability") or "").strip() or None
    medication = str(payload.get("medication_name") or "").strip() or None
    language = str(payload.get("language") or "").strip() or None
    location = str(payload.get("location") or "").strip() or None
    return IntakeRequest(
        care_task=_choice(payload, "care_task", "symptom_first"),
        confirmed_capability=capability,
        location=location,
        urgency=_choice(payload, "urgency", "routine"),
        travel_tolerance=_choice(payload, "travel_tolerance", "medium"),
        budget_sensitivity=_choice(payload, "budget_sensitivity", "medium"),
        facility_preference=_choice(payload, "facility_preference", "either"),
        language_preference=language,
        medication_name=medication,
        has_current_prescription=payload.get("has_current_prescription"),
        has_clinician_order=payload.get("has_clinician_order"),
        user_confirmed=True,
        emergency_warning_reported=bool(payload.get("emergency_warning_reported", False)),
    )


def evaluate_demo_request(payload: dict[str, Any]) -> DemoOutcome:
    """Apply blocking safety/validation gates before returning demo content."""

    request = build_confirmed_request(payload)
    if request.emergency_warning_reported or request.urgency == "emergency":
        return DemoOutcome(
            safety_branch=SafetyBranch.EMERGENCY,
            message="Emergency warning reported. Seek urgent local help now; Aven will not rank ordinary options.",
        )

    if request.care_task == "symptom_first" and not request.confirmed_capability:
        return DemoOutcome(
            safety_branch=SafetyBranch.CONFIRM_CARE_SETTING,
            message="Confirm a possible first care setting before Aven searches for facilities.",
        )

    errors = validate_confirmed_intake(request)
    if errors:
        return DemoOutcome(
            safety_branch=SafetyBranch.INCOMPLETE_INTAKE,
            message="Complete the missing information before Aven creates a plan.",
            validation_errors=errors,
        )

    display_payload = dict(payload)
    display_payload["capability"] = request.confirmed_capability or request.medication_name or "the confirmed care need"
    return DemoOutcome(
        safety_branch=SafetyBranch.PROCEED,
        options=tuple(build_demo_options(display_payload)),
    )
