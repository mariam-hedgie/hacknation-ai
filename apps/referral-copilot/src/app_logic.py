"""Framework-independent orchestration for Aven's confirmed demo journey."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .demo_adapter import build_demo_options
from .domain import IntakeRequest, SafetyBranch, validate_confirmed_intake

# A planner turns a confirmed, gate-cleared payload into display-shaped options.
# Injecting it keeps this module framework- and backend-independent: the demo
# adapter is the default, and `ui_contract` supplies the live Databricks-backed
# `backend.service.plan_routes` without the gates moving or being duplicated.
Planner = Callable[[dict[str, Any]], list[dict[str, Any]]]


@dataclass(frozen=True)
class PlanOutcome:
    """Safe result passed to the UI after confirmation."""

    safety_branch: SafetyBranch
    options: tuple[dict[str, Any], ...] = ()
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
        max_distance_km=payload.get("max_distance_km"),
        travel_modes=tuple(payload.get("travel_modes") or ()),
        travel_budget_rupees=payload.get("travel_budget_rupees"),
        care_budget_rupees=payload.get("care_budget_rupees"),
        facility_preference=_choice(payload, "facility_preference", "either"),
        language_preference=language,
        medication_name=medication,
        has_current_prescription=payload.get("has_current_prescription"),
        has_clinician_order=payload.get("has_clinician_order"),
        user_confirmed=True,
        emergency_warning_reported=bool(payload.get("emergency_warning_reported", False)),
    )


def evaluate_confirmed_request(
    payload: dict[str, Any], *, planner: Planner = build_demo_options
) -> PlanOutcome:
    """Apply blocking safety/validation gates before any planner runs.

    Every gate below is blocking: the planner is only reached on PROCEED, so no
    route options can be produced for an emergency, an unconfirmed care setting,
    or an incomplete intake.
    """

    request = build_confirmed_request(payload)
    if request.emergency_warning_reported or request.urgency == "emergency":
        return PlanOutcome(
            safety_branch=SafetyBranch.EMERGENCY,
            message="Emergency warning reported. Seek urgent local help now; Aven will not rank ordinary options.",
        )

    if request.care_task == "symptom_first" and not request.confirmed_capability:
        return PlanOutcome(
            safety_branch=SafetyBranch.CONFIRM_CARE_SETTING,
            message="Confirm a possible first care setting before Aven searches for facilities.",
        )

    errors = validate_confirmed_intake(request)
    if errors:
        return PlanOutcome(
            safety_branch=SafetyBranch.INCOMPLETE_INTAKE,
            message="Complete the missing information before Aven creates a plan.",
            validation_errors=errors,
        )

    display_payload = dict(payload)
    display_payload["capability"] = request.confirmed_capability or request.medication_name or "the confirmed care need"
    return PlanOutcome(
        safety_branch=SafetyBranch.PROCEED,
        options=tuple(planner(display_payload)),
    )
