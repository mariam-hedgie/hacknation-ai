"""ReferralService — the single seam the frontend calls.

Orchestrates the evidence pipeline (Vector Search -> Agent Bricks -> domain
ranking) inside an MLflow span, and persists user state via Lakebase. Every
external step is a stub that returns None today, so `plan_routes` cleanly falls
back to the deterministic seeded demo options and the app runs unchanged.

The frontend imports display-shaped dicts from here; it never imports a
Databricks tool directly.
"""

from __future__ import annotations

from typing import Any

from .. import enrichment
from ..demo_adapter import build_demo_options
from ..domain import (
    FacilityCandidate,
    IntakeRequest,
    RankedOption,
    ShortlistResult,
    SafetyBranch,
    build_shortlist,
)
from . import tracing
from .agent_bricks import AgentBricksClient
from .config import BackendConfig
from .genie import GenieClient
from .lakebase import LakebasePersistence
from .local_ask import LocalAskClient
from .local_search import LocalDataRetriever
from .vector_search import VectorSearchClient

_CONFIG = BackendConfig.from_env()
_vector_search = VectorSearchClient(_CONFIG)
_local_search = LocalDataRetriever()
_agent = AgentBricksClient(_CONFIG)
_genie = GenieClient(_CONFIG)
_local_ask = LocalAskClient(_local_search)  # shares the loaded snapshot with _local_search
_persistence = LakebasePersistence(_CONFIG)


# ---------- Status ----------

def backend_mode() -> str:
    """"live" or "demo" — drives the honest data-source badge in the UI."""
    return _CONFIG.mode()


def status() -> dict[str, bool]:
    """Per-tool availability, for a diagnostics panel."""
    return {
        "sql": _CONFIG.has_sql,
        "vector_search": _CONFIG.has_vector_search,
        "agent_bricks": _CONFIG.has_agent,
        "genie": _CONFIG.has_genie,
        "lakebase": _CONFIG.has_lakebase,
        "mlflow": _CONFIG.has_mlflow,
        # Real facility data from a local snapshot (data/facilities_searchable.json),
        # not a live Databricks connection — see local_search.py. Lets the UI say
        # "real data, local snapshot" instead of lumping it in with seeded demo
        # content just because backend_mode() isn't "live".
        "local_data": _local_search.available(),
        # Local stand-in for Genie: an LLM extracts a filter, the answer/rows
        # come from the local snapshot. See local_ask.py. Lets the Ask page's
        # submit button enable even when Genie/Databricks aren't configured.
        "local_ask": _local_ask.available(),
    }


# ---------- Referral shortlist ----------

def plan_routes(request: dict[str, Any]) -> list[dict[str, Any]]:
    """Return display-shaped route options for a confirmed request.

    Tries the live evidence pipeline; falls back to seeded demo options until
    Vector Search + Agent Bricks are wired.
    """
    with tracing.span(
        "referral.plan_routes",
        inputs={"care_task": request.get("care_task"), "capability": request.get("capability")},
        care_task=str(request.get("care_task")),
    ) as plan_span:
        live = _live_plan_routes(request)
        options = live if live is not None else build_demo_options(request)
        plan_span.set_outputs({"backend_mode": backend_mode(), "option_count": len(options)})
        return options


def _live_plan_routes(request: dict[str, Any]) -> list[dict[str, Any]] | None:
    """The real pipeline. Returns None (→ demo fallback) whenever any required
    stage is unavailable, so partial wiring never crashes a demo."""
    capability = str(request.get("capability") or "")
    location = request.get("location")

    with tracing.span(
        "vector_search.retrieve", inputs={"capability": capability, "location": location}
    ) as retrieve_span:
        rows = _vector_search.retrieve(capability, location)
        retrieve_span.set_outputs({"row_count": len(rows) if rows is not None else 0, "available": rows is not None})

    if rows is None:
        # No live Vector Search configured/reachable — fall back to the local
        # real-data snapshot (still real facility data, just not a live
        # connection) before giving up to seeded demo options entirely.
        with tracing.span(
            "local_search.retrieve", inputs={"capability": capability, "location": location}
        ) as local_span:
            rows = _local_search.retrieve(capability, location)
            local_span.set_outputs({"row_count": len(rows) if rows is not None else 0, "available": rows is not None})

    if rows is None:
        return None

    with tracing.span(
        "agent_bricks.assess_claims", inputs={"capability": capability, "row_count": len(rows)}
    ) as assess_span:
        candidates = _agent.assess_claims(
            rows, capability=capability, location=str(location or "")
        )
        assess_span.set_outputs(
            {
                "candidate_count": len(candidates) if candidates is not None else 0,
                "evidence_status_counts": _status_counts(candidates) if candidates else {},
            }
        )
    if candidates is None:
        return None

    try:
        intake = _intake_from_request(request)
        with tracing.span(
            "domain.build_shortlist",
            inputs={"care_task": intake.care_task, "candidate_count": len(candidates)},
        ) as shortlist_span:
            result: ShortlistResult = build_shortlist(intake, candidates)
            shortlist_span.set_outputs(
                {"safety_branch": result.safety_branch.value, "option_count": len(result.options)}
            )
        if result.safety_branch is not SafetyBranch.PROCEED or not result.options:
            return None
        return [_ranked_to_display(opt, i) for i, opt in enumerate(result.options)]
    except Exception:
        # Any mapping/ranking issue must not break the live demo: use demo data.
        return None


def _status_counts(candidates: list[FacilityCandidate]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        key = candidate.evidence_status.value
        counts[key] = counts.get(key, 0) + 1
    return counts


_LABELS = ("Best documented fit", "Lower-burden route", "Alternative to verify")


def _intake_from_request(request: dict[str, Any]) -> IntakeRequest:
    """Map the UI's confirmed request dict onto the domain IntakeRequest.

    The task-specific fields matter: build_shortlist re-runs
    validate_confirmed_intake, so dropping them here would fail every refill on
    the live path even though the intake form collects them.
    """
    return IntakeRequest(
        care_task=str(request.get("care_task") or "known_referral"),
        confirmed_capability=(request.get("capability") or None),
        location=(request.get("location") or None),
        urgency=str(request.get("urgency") or "routine").lower(),
        travel_tolerance=str(request.get("travel_tolerance") or "medium").lower(),
        budget_sensitivity=str(request.get("budget_sensitivity") or "medium").lower(),
        max_distance_km=request.get("max_distance_km"),
        travel_modes=tuple(request.get("travel_modes") or ()),
        travel_budget_rupees=request.get("travel_budget_rupees"),
        care_budget_rupees=request.get("care_budget_rupees"),
        required_arrival_date=(request.get("required_arrival_date") or None),
        facility_preference=str(request.get("facility_preference") or "either").lower(),
        language_preference=(request.get("language") or None),
        medication_name=(request.get("medication_name") or None),
        has_current_prescription=request.get("has_current_prescription"),
        has_clinician_order=request.get("has_clinician_order"),
        emergency_warning_reported=bool(request.get("emergency_warning_reported", False)),
        user_confirmed=True,
    )


def _ranked_to_display(option: RankedOption, index: int) -> dict[str, Any]:
    """Convert a domain RankedOption into the card dict the UI renders."""
    c = option.candidate
    distance = (
        f"approximately {c.distance_km:g} km straight-line from the named city centre; "
        "open Maps for route distance"
        if c.distance_km is not None
        else "Distance not documented — confirm before travel."
    )
    unknowns = ", ".join(f.replace("_", " ") for f in c.missing_fields) or "None flagged by the evidence pipeline."
    evidence = " | ".join(c.source_spans) if c.source_spans else "No literal source span was verified for this claim."
    return {
        "label": _LABELS[min(index, len(_LABELS) - 1)],
        "facility": c.display_name,
        "summary": f"Documented match for {c.capability}." if c.capability else "Candidate facility.",
        "travel": f"Travel estimate: {distance}",
        "cost": "Consultation price: not confirmed — call before leaving.",
        "evidence": evidence,
        "unknowns": f"We could not confirm: {unknowns}",
        "next_step": "Call the official facility contact to confirm the service is currently available.",
        "ranking": "; ".join(option.reasons) or "Ranked by documented evidence and your preferences.",
        "evidence_status": c.evidence_status.value,
        "enrichment": enrichment.normalize(c.enrichment),
    }


# ---------- Planner data questions (Genie seam) ----------

def ask_data_question(question: str, *, conversation_id: str | None = None) -> dict[str, Any] | None:
    """Answer a free-text planner question against the facility tables.

    Tries Genie (live Databricks NL -> SQL) first; falls back to LocalAskClient
    (an LLM extracts a capability filter, the answer/rows come straight back out
    of the local snapshot — never from the LLM's own "knowledge") when Genie
    isn't configured. Returns None when neither is available or the question
    can't be answered — callers must show an honest "not answered" state, never
    a fabricated one. The returned `sql` should be shown alongside the answer
    as its evidence.
    """
    with tracing.span("genie.ask", inputs={"question": question}) as ask_span:
        result = _genie.ask(question, conversation_id=conversation_id)
        ask_span.set_outputs({"answered": result is not None})

    if result is None:
        with tracing.span("local_ask.ask", inputs={"question": question}) as local_ask_span:
            result = _local_ask.ask(question, conversation_id=conversation_id)
            local_ask_span.set_outputs({"answered": result is not None})

    return result


# ---------- Persistence (Lakebase seam) ----------

def load_profile(email: str) -> dict[str, Any]:
    return _persistence.load_profile(email)


def save_profile(profile: dict[str, Any]) -> None:
    _persistence.save_profile(profile)
