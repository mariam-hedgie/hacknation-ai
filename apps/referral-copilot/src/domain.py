"""Pure, deterministic domain rules for Aven's care-access planner.

This module deliberately does not diagnose, prescribe, call external services,
or treat missing information as a negative fact.  Adapters may build these
objects from Databricks tables or conversational input, but all search/ranking
must pass through a confirmed request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Iterable


class EvidenceStatus(str, Enum):
    """User-visible evidence states prescribed by the product plan."""

    DOCUMENTED = "documented"
    CONFLICTING = "conflicting"
    NOT_DOCUMENTED = "not_documented"
    EXTERNAL_CORROBORATED = "external_corroborated"


class SafetyBranch(str, Enum):
    """The route the UI must take before it may show facility ranking."""

    PROCEED = "proceed"
    EMERGENCY = "emergency"
    CONFIRM_CARE_SETTING = "confirm_care_setting"
    INCOMPLETE_INTAKE = "incomplete_intake"


_CARE_TASKS = frozenset(
    {"known_referral", "procedure", "lab", "refill", "vaccination", "symptom_first", "follow_up"}
)
_URGENCY = frozenset({"routine", "soon", "urgent", "emergency"})
_PREFERENCES = frozenset({"public", "private", "either", "unknown"})
_SENSITIVITY = frozenset({"low", "medium", "high"})


@dataclass(frozen=True)
class IntakeRequest:
    """Editable user information after extraction, before any search occurs."""

    care_task: str
    confirmed_capability: str | None = None
    location: str | None = None
    urgency: str = "routine"
    travel_tolerance: str = "medium"
    budget_sensitivity: str = "medium"
    max_distance_km: int | None = None
    travel_modes: tuple[str, ...] = ()
    travel_budget_rupees: int | None = None
    care_budget_rupees: int | None = None
    required_arrival_date: str | None = None
    facility_preference: str = "either"
    language_preference: str | None = None
    medication_name: str | None = None
    has_current_prescription: bool | None = None
    has_clinician_order: bool | None = None
    user_confirmed: bool = False
    emergency_warning_reported: bool = False


@dataclass(frozen=True)
class FacilityCandidate:
    """A capability candidate assembled only from source-grounded data."""

    facility_id: str
    display_name: str
    capability: str
    evidence_status: EvidenceStatus
    distance_km: float | None = None
    facility_type: str | None = None
    missing_fields: tuple[str, ...] = ()
    source_spans: tuple[str, ...] = ()
    # Normalized extractor output (see enrichment.normalize). Carried for display
    # only: ranking reads evidence_status, never this blob, so a richer record can
    # never out-rank a documented one just for having more extracted text.
    enrichment: dict | None = None
    estimated_journey_minutes: int | None = None
    estimated_travel_cost_rupees: int | None = None
    arrival_feasible: bool | None = None


@dataclass(frozen=True)
class RankedOption:
    candidate: FacilityCandidate
    score: int
    reasons: tuple[str, ...]
    cautions: tuple[str, ...]


@dataclass(frozen=True)
class ShortlistResult:
    safety_branch: SafetyBranch
    options: tuple[RankedOption, ...] = ()
    message: str | None = None
    validation_errors: tuple[str, ...] = ()


def _present(value: str | None) -> bool:
    return bool(value and value.strip())


def _valid_choice(value: str, choices: frozenset[str]) -> bool:
    return value in choices


def validate_confirmed_intake(request: IntakeRequest) -> tuple[str, ...]:
    """Return all blocking errors instead of silently guessing user intent."""

    errors: list[str] = []
    if request.care_task not in _CARE_TASKS:
        errors.append("Choose a supported care task before searching.")
    if not request.user_confirmed:
        errors.append("Confirm the request before searching for facilities.")
    if not _present(request.location):
        errors.append("Add a location before searching for facilities.")
    if not _valid_choice(request.urgency, _URGENCY):
        errors.append("Choose a valid urgency level.")
    if not _valid_choice(request.travel_tolerance, _SENSITIVITY):
        errors.append("Choose a valid travel tolerance.")
    if not _valid_choice(request.budget_sensitivity, _SENSITIVITY):
        errors.append("Choose a valid budget sensitivity.")
    if not _valid_choice(request.facility_preference, _PREFERENCES):
        errors.append("Choose a valid facility preference.")
    if request.max_distance_km is not None and request.max_distance_km < 1:
        errors.append("Maximum travel distance must be at least 1 km.")
    if request.travel_budget_rupees is not None and request.travel_budget_rupees < 0:
        errors.append("Travel budget cannot be negative.")
    if request.care_budget_rupees is not None and request.care_budget_rupees < 0:
        errors.append("Care budget cannot be negative.")
    if request.required_arrival_date:
        try:
            date.fromisoformat(request.required_arrival_date)
        except (TypeError, ValueError):
            errors.append("Choose a valid required-arrival date.")

    if request.care_task in {"known_referral", "procedure", "lab", "follow_up"} and not _present(
        request.confirmed_capability
    ):
        errors.append("Add the requested specialty, service, or procedure.")
    if request.care_task == "refill":
        if not _present(request.medication_name):
            errors.append("Add the medicine name before planning a refill route.")
        if request.has_current_prescription is not True:
            errors.append(
                "Aven can only plan a refill route when a current prescription or refill instruction is confirmed."
            )
    if request.care_task == "lab" and request.has_clinician_order is False:
        errors.append("Confirm whether a clinician has provided a test order or referral.")
    return tuple(errors)


def evidence_status(
    source_text: str | None,
    cited_span: str | None,
    *,
    has_conflict: bool = False,
    external_corroborated: bool = False,
) -> EvidenceStatus:
    """Classify a claim only after checking its literal evidence span.

    A conflict is shown before any positive badge.  An external source may be
    corroborating only when the original literal citation remains valid.
    """

    if has_conflict:
        return EvidenceStatus.CONFLICTING
    if not _present(source_text) or not _present(cited_span):
        return EvidenceStatus.NOT_DOCUMENTED
    if cited_span.casefold() not in source_text.casefold():
        return EvidenceStatus.NOT_DOCUMENTED
    if external_corroborated:
        return EvidenceStatus.EXTERNAL_CORROBORATED
    return EvidenceStatus.DOCUMENTED


def _normalise_capability(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _matches_confirmed_need(request: IntakeRequest, candidate: FacilityCandidate) -> bool:
    """Require source-backed capability matches; never infer a synonym here."""

    if request.care_task == "refill":
        # Pharmacy data is only a valid option once an upstream adapter has
        # represented it as a documented service candidate.
        return candidate.evidence_status in {
            EvidenceStatus.DOCUMENTED,
            EvidenceStatus.EXTERNAL_CORROBORATED,
        }
    needed = _normalise_capability(request.confirmed_capability)
    return bool(needed) and needed == _normalise_capability(candidate.capability) and candidate.evidence_status in {
        EvidenceStatus.DOCUMENTED,
        EvidenceStatus.EXTERNAL_CORROBORATED,
        EvidenceStatus.CONFLICTING,
    }


def _rank_candidate(request: IntakeRequest, candidate: FacilityCandidate) -> RankedOption:
    score = 0
    reasons: list[str] = []
    cautions: list[str] = []

    if candidate.evidence_status == EvidenceStatus.EXTERNAL_CORROBORATED:
        score += 100
        reasons.append("documented capability evidence with an official external source")
    elif candidate.evidence_status == EvidenceStatus.DOCUMENTED:
        score += 90
        reasons.append("documented capability evidence")
    else:
        # Conflicting evidence can be an alternative but can never outrank a
        # documented match merely because it is closer.
        score += 20
        cautions.append("conflicting facility details")

    if candidate.distance_km is not None:
        distance = max(candidate.distance_km, 0)
        travel_weight = {"low": 5, "medium": 3, "high": 1}[request.travel_tolerance]
        score -= round(distance * travel_weight)
        reasons.append(f"{distance:g} km from the entered location")
    else:
        cautions.append("distance not documented")

    if request.required_arrival_date:
        if candidate.arrival_feasible is True:
            score += 50
            reasons.append(f"can plausibly arrive by {request.required_arrival_date}")
        elif candidate.arrival_feasible is False:
            score -= 150
            cautions.append(f"may miss the requested arrival date {request.required_arrival_date}")
        else:
            cautions.append("arrival-by feasibility not confirmed")

    if candidate.estimated_journey_minutes is not None:
        minutes = max(candidate.estimated_journey_minutes, 0)
        score -= round(minutes / 15)
        reasons.append(f"estimated journey time considered: {minutes} minutes")

    if request.travel_budget_rupees is not None:
        travel_cost = candidate.estimated_travel_cost_rupees
        if travel_cost is None:
            cautions.append("travel cost not confirmed")
        elif travel_cost <= request.travel_budget_rupees:
            score += 15
            reasons.append("estimated travel cost fits your stated travel budget")
        else:
            score -= 30
            cautions.append("estimated travel cost exceeds your stated travel budget")

    normalised_type = (candidate.facility_type or "").casefold()
    if request.facility_preference in {"public", "private"}:
        if normalised_type == request.facility_preference:
            score += 12
            reasons.append(f"matches your {request.facility_preference} facility preference")
        elif normalised_type:
            cautions.append(f"does not match your {request.facility_preference} facility preference")
        else:
            cautions.append("facility type not documented")

    # Facility type can signal a stated preference only; it never becomes a
    # fabricated consultation price.
    if request.budget_sensitivity == "high":
        if normalised_type == "public":
            score += 8
            reasons.append("public-facility preference considered; price still needs confirmation")
        elif not normalised_type and "facility type not documented" not in cautions:
            cautions.append("facility type not documented")

    for field_name in candidate.missing_fields:
        label = field_name.replace("_", " ")
        caution = f"{label} not documented"
        if caution not in cautions:
            cautions.append(caution)

    return RankedOption(candidate, score, tuple(reasons), tuple(cautions))


def build_shortlist(
    request: IntakeRequest, candidates: Iterable[FacilityCandidate]
) -> ShortlistResult:
    """Build a transparent facility shortlist without hidden clinical logic."""

    if request.emergency_warning_reported or request.urgency == "emergency":
        return ShortlistResult(
            SafetyBranch.EMERGENCY,
            message="Emergency warning reported. Do not continue normal facility ranking; seek urgent help now.",
        )

    if request.care_task == "symptom_first" and not _present(request.confirmed_capability):
        return ShortlistResult(
            SafetyBranch.CONFIRM_CARE_SETTING,
            message="Confirm a possible first care setting before Aven searches for facilities.",
        )

    errors = validate_confirmed_intake(request)
    if errors:
        return ShortlistResult(
            SafetyBranch.INCOMPLETE_INTAKE,
            message="Complete and confirm the request before Aven creates a plan.",
            validation_errors=errors,
        )

    eligible = [
        candidate
        for candidate in candidates
        if _matches_confirmed_need(request, candidate)
        and (
            request.max_distance_km is None
            or (
                candidate.distance_km is not None
                and candidate.distance_km <= request.max_distance_km
            )
        )
    ]
    if not eligible:
        message = "No documented facility match was found for this confirmed need."
        if request.max_distance_km is not None:
            message = (
                f"Aven could not verify a documented facility within {request.max_distance_km:g} km "
                "of the entered location. Increase the limit or verify a facility in Maps."
            )
        return ShortlistResult(
            SafetyBranch.PROCEED,
            message=message,
        )

    options = sorted(
        (_rank_candidate(request, candidate) for candidate in eligible),
        key=lambda option: (-option.score, option.candidate.display_name.casefold(), option.candidate.facility_id),
    )
    return ShortlistResult(SafetyBranch.PROCEED, tuple(options[:3]))
