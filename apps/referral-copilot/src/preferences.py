"""Concrete, source-honest planning preferences for Aven."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Sequence


def normalize_optional_rupees(value: object) -> int | None:
    """Normalize a user-entered rupee cap; zero means no limit supplied."""

    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("Rupee limits must be numeric.")
    amount = int(value)
    if amount < 0:
        raise ValueError("Rupee limits cannot be negative.")
    return amount or None


@dataclass(frozen=True)
class BudgetFit:
    travel_status: str
    care_status: str
    summary: str


def _compare(limit: int | None, sourced_amount: int | None) -> str:
    if limit is None:
        return "no_limit"
    if sourced_amount is None:
        return "not_confirmed"
    return "within_budget" if sourced_amount <= limit else "over_budget"


def budget_fit(
    *,
    travel_budget_rupees: int | None,
    care_budget_rupees: int | None,
    estimated_travel_cost_rupees: int | None,
    documented_care_cost_rupees: int | None,
) -> BudgetFit:
    """Compare only sourced amounts with user caps; unknown never becomes a fit."""

    travel = _compare(travel_budget_rupees, estimated_travel_cost_rupees)
    care = _compare(care_budget_rupees, documented_care_cost_rupees)
    labels = {
        "no_limit": "no limit entered",
        "not_confirmed": "amount not confirmed",
        "within_budget": "within entered limit",
        "over_budget": "above entered limit",
    }
    return BudgetFit(
        travel_status=travel,
        care_status=care,
        summary=f"Travel: {labels[travel]}. Care: {labels[care]}.",
    )


def summarize_preferences(
    *,
    max_distance_km: int,
    travel_modes: Sequence[str],
    travel_budget_rupees: int | None,
    care_budget_rupees: int | None,
) -> str:
    parts = [f"up to {max_distance_km:,} km", f"travel by {', '.join(travel_modes)}"]
    if travel_budget_rupees:
        parts.append(f"travel budget ₹{travel_budget_rupees:,}")
    if care_budget_rupees:
        parts.append(f"care budget ₹{care_budget_rupees:,}")
    return "; ".join(parts)
