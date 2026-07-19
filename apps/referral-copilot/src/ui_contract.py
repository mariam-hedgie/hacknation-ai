"""Stable façade for independently developed Aven user interfaces.

UI owners should depend on this module instead of importing Streamlit or
reimplementing safety, evidence, persistence, localization, or map rules.
The façade contains no visual decisions, so `app.py` can be replaced freely.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any

from .app_logic import evaluate_confirmed_request
from .backend.service import plan_routes
from .databricks_adapter import (
    ConfigurationError,
    SessionLocalPlanStore,
    load_databricks_config,
)
from .localization import translate_core, voice_provider_status
from .maps import mode_capability, select_map_provider


_FEEDBACK_STATUSES = frozenset(
    {
        "helpful",
        "needs_correction",
        "not_sure",
        "service_unavailable",
        "price_differed",
        "accepted",
        "not_visited",
    }
)
_PLAN_INDEX_KEY = "aven_ui_plan_index"


@dataclass(frozen=True)
class UiPlanResponse:
    """Framework-neutral response consumed by the result and safety screens."""

    safety_branch: str
    options: tuple[dict[str, Any], ...] = ()
    message: str | None = None
    validation_errors: tuple[str, ...] = ()


class AvenUiBackend:
    """Thin, stable integration surface matching `docs/ui-handoff.md`."""

    def __init__(
        self,
        session_state: MutableMapping[str, object],
        *,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._state = session_state
        self._env = os.environ if env is None else env
        self._store = SessionLocalPlanStore(session_state)
        self._state.setdefault(_PLAN_INDEX_KEY, {})

    def _plan_index(self) -> MutableMapping[str, list[str]]:
        index = self._state[_PLAN_INDEX_KEY]
        if not isinstance(index, MutableMapping):
            raise TypeError("UI plan index must be a mutable mapping")
        return index

    def confirm_and_plan(self, confirmed_request: Mapping[str, Any]) -> UiPlanResponse:
        """Apply the shared blocking gates, then plan through the live backend.

        This is the only planning entry point the UI should use. The gates run
        first and are blocking; `backend.service.plan_routes` runs only on
        PROCEED, and itself falls back to seeded demo options whenever the
        Databricks pipeline is unavailable, so the demo path stays intact.
        """

        outcome = evaluate_confirmed_request(
            dict(confirmed_request), planner=plan_routes
        )
        return UiPlanResponse(
            safety_branch=outcome.safety_branch.value,
            options=outcome.options,
            message=outcome.message,
            validation_errors=outcome.validation_errors,
        )

    def save_plan(
        self,
        confirmed_request: Mapping[str, object],
        selected_option: Mapping[str, object],
        next_steps: Sequence[str],
        *,
        plan_id: str,
    ) -> dict[str, object]:
        """Save the UI handoff shape without blending user context into evidence."""

        demo_user_id = str(confirmed_request.get("demo_user_id") or "demo-user")
        saved = self._store.save_plan(
            {
                "plan_id": plan_id,
                "demo_user_id": demo_user_id,
                "confirmed_request": dict(confirmed_request),
                "selected_option": dict(selected_option),
                "next_steps": list(next_steps),
            }
        )
        user_plans = self._plan_index().setdefault(demo_user_id, [])
        if plan_id not in user_plans:
            user_plans.append(plan_id)
        return saved

    def save_override(
        self,
        plan_id: str,
        facility_id: str,
        note: str,
        *,
        selected_despite_rank: bool = True,
    ) -> dict[str, object]:
        """Persist a user's choice separately from source-backed option evidence."""

        plan = self.load_plan(plan_id)
        if plan is None:
            raise KeyError(f"Unknown plan_id: {plan_id}")
        plan["user_override"] = {
            "facility_id": facility_id.strip(),
            "note": note.strip(),
            "selected_despite_rank": bool(selected_despite_rank),
        }
        return self._store.save_plan(plan)

    def save_feedback(
        self, plan_id: str, status: str, optional_note: str = ""
    ) -> dict[str, object]:
        normalized = status.strip().casefold()
        if normalized not in _FEEDBACK_STATUSES:
            raise ValueError("Choose one of Aven's bounded feedback statuses.")
        if self.load_plan(plan_id) is None:
            raise KeyError(f"Unknown plan_id: {plan_id}")
        return self._store.save_feedback(
            plan_id, {"status": normalized, "note": optional_note.strip()}
        )

    def load_plan(self, plan_id: str) -> dict[str, object] | None:
        return self._store.get_plan(plan_id)

    def load_saved_plans(self, demo_user_id: str) -> tuple[dict[str, object], ...]:
        plan_ids = self._plan_index().get(demo_user_id, [])
        plans = (self.load_plan(plan_id) for plan_id in plan_ids)
        return tuple(plan for plan in plans if plan is not None)

    def travel_capabilities(
        self, modes: Sequence[str]
    ) -> tuple[dict[str, object], ...]:
        provider = select_map_provider(self._env)
        rows: list[dict[str, object]] = []
        for mode in modes:
            capability = mode_capability(provider, mode)
            rows.append(
                {
                    "mode": capability.mode,
                    "provider": provider.name,
                    "route_supported": capability.route_supported,
                    "comparison_only": capability.comparison_only,
                    "live_price_supported": capability.live_price_supported,
                    "live_transit_supported": capability.live_transit_supported,
                    "label": capability.user_label,
                }
            )
        return tuple(rows)

    def copy(self, key: str, language: object) -> dict[str, object]:
        translated = translate_core(key, language)
        return {
            "text": translated.text,
            "language": translated.language.code,
            "used_fallback": translated.language.used_fallback,
            "fallback_message": translated.language.fallback_message,
        }

    def service_status(self) -> dict[str, object]:
        """Expose capability state only; never credential values or identifiers."""

        provider = select_map_provider(self._env)
        voice = voice_provider_status(self._env)
        try:
            databricks_mode = (
                "configured"
                if load_databricks_config(self._env) is not None
                else "disconnected"
            )
        except ConfigurationError:
            databricks_mode = "misconfigured"
        return {
            "map_provider": provider.name,
            "map_live_provider": provider.is_live_provider,
            "voice_available": voice.available,
            "voice_message": voice.public_message,
            "databricks_mode": databricks_mode,
        }
