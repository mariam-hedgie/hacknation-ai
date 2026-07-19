"""Safe Databricks boundaries for facility evidence and interactive state.

The module deliberately performs no network connection by itself.  Databricks
Apps can inject an authenticated SQL executor that uses the app identity; local
development remains explicitly disconnected.  Personal access tokens are not
part of this adapter's configuration contract.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Protocol, Sequence

from .domain import EvidenceStatus, FacilityCandidate, evidence_status
from .maps import validate_coordinates


class ConfigurationError(ValueError):
    """Raised when only part of the required Databricks resource is configured."""


@dataclass(frozen=True)
class DatabricksConfig:
    """Non-secret SQL endpoint coordinates supplied by a Databricks App."""

    server_hostname: str
    http_path: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "DatabricksConfig":
        source = os.environ if environ is None else environ
        hostname = source.get("DATABRICKS_SERVER_HOSTNAME", "").strip()
        http_path = source.get("DATABRICKS_HTTP_PATH", "").strip()
        missing = [
            name
            for name, value in (
                ("DATABRICKS_SERVER_HOSTNAME", hostname),
                ("DATABRICKS_HTTP_PATH", http_path),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError(
                "Missing required Databricks configuration: " + ", ".join(missing)
            )
        return cls(server_hostname=hostname, http_path=http_path)


def load_databricks_config(
    environ: Mapping[str, str] | None = None,
) -> DatabricksConfig | None:
    """Load a complete config or select safe disconnected mode when both fields are absent."""

    source = os.environ if environ is None else environ
    hostname = source.get("DATABRICKS_SERVER_HOSTNAME", "").strip()
    http_path = source.get("DATABRICKS_HTTP_PATH", "").strip()
    if not hostname and not http_path:
        return None
    return DatabricksConfig.from_env(source)


class SqlExecutor(Protocol):
    """Small injectable SQL surface; implementations must bind parameters."""

    def execute(
        self, statement: str, parameters: tuple[object, ...]
    ) -> Sequence[Mapping[str, object]]: ...


@dataclass(frozen=True)
class FacilityQueryResult:
    candidates: tuple[FacilityCandidate, ...]
    connected: bool
    message: str


_FACILITY_QUERY = """
SELECT
    f.facility_id,
    f.display_name,
    e.capability,
    t.data_status,
    t.contradiction_flag,
    CAST(NULL AS DOUBLE) AS distance_km,
    f.facility_type,
    t.missing_fields,
    e.literal_source_text,
    e.cited_span,
    e.source_column,
    e.source_row_id
FROM facilities_normalized AS f
JOIN facility_claims_evidence AS e ON e.facility_id = f.facility_id
LEFT JOIN facility_trust_assessment AS t
    ON t.facility_id = e.facility_id AND t.capability = e.capability
WHERE e.capability = ?
LIMIT ?
""".strip()


_NEARBY_FACILITY_QUERY = """
WITH matched AS (
  SELECT
    f.facility_id,
    f.display_name,
    e.capability,
    t.data_status,
    t.contradiction_flag,
    6371 * 2 * asin(
      sqrt(
        pow(sin((radians(f.lat) - radians(?)) / 2), 2)
        + cos(radians(?)) * cos(radians(f.lat))
        * pow(sin((radians(f.lon) - radians(?)) / 2), 2)
      )
    ) AS distance_km,
    f.facility_type,
    t.missing_fields,
    e.literal_source_text,
    e.cited_span,
    e.source_column,
    e.source_row_id,
    row_number() OVER (
      PARTITION BY f.facility_id
      ORDER BY t.corroboration_count DESC, e.source_column, e.evidence_id
    ) AS evidence_rank
  FROM facilities_normalized AS f
  JOIN facility_claims_evidence AS e ON e.facility_id = f.facility_id
  LEFT JOIN facility_trust_assessment AS t
    ON t.facility_id = e.facility_id AND t.capability = e.capability
  WHERE f.lat IS NOT NULL
    AND f.lon IS NOT NULL
    AND e.capability = ?
)
SELECT
  facility_id,
  display_name,
  capability,
  data_status,
  contradiction_flag,
  distance_km,
  facility_type,
  missing_fields,
  literal_source_text,
  cited_span,
  source_column,
  source_row_id
FROM matched
WHERE evidence_rank = 1
ORDER BY distance_km, display_name
LIMIT ?
""".strip()


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _parse_missing_fields(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    parsed: object = value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in stripped.split(",")]
    if isinstance(parsed, (list, tuple, set)):
        return tuple(dict.fromkeys(_text(item) for item in parsed if _text(item)))
    text = _text(parsed)
    return (text,) if text else ()


def _distance(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _translate_row(row: Mapping[str, object]) -> FacilityCandidate:
    literal_source_text = _text(row.get("literal_source_text"))
    cited_span = _text(row.get("cited_span"))
    data_status = _text(row.get("data_status")).casefold()
    has_conflict = bool(row.get("contradiction_flag")) or data_status == "conflicting"
    external = data_status == "external_corroborated"
    status = evidence_status(
        literal_source_text,
        cited_span,
        has_conflict=has_conflict,
        external_corroborated=external,
    )

    missing_fields = list(_parse_missing_fields(row.get("missing_fields")))
    verified_span = status in {
        EvidenceStatus.DOCUMENTED,
        EvidenceStatus.CONFLICTING,
        EvidenceStatus.EXTERNAL_CORROBORATED,
    } and bool(cited_span) and cited_span.casefold() in literal_source_text.casefold()
    if not verified_span and "evidence_span" not in missing_fields:
        missing_fields.append("evidence_span")

    source_spans: tuple[str, ...] = ()
    if verified_span:
        source_column = _text(row.get("source_column")) or "source"
        source_row_id = _text(row.get("source_row_id")) or "row not documented"
        source_spans = (f"{source_column} [{source_row_id}]: {cited_span}",)

    return FacilityCandidate(
        facility_id=_text(row.get("facility_id")),
        display_name=_text(row.get("display_name")) or "Facility name not documented",
        capability=_text(row.get("capability")),
        evidence_status=status,
        distance_km=_distance(row.get("distance_km")),
        facility_type=_text(row.get("facility_type")) or None,
        missing_fields=tuple(missing_fields),
        source_spans=source_spans,
    )


class DatabricksFacilityRepository:
    """Read source-backed facility candidates through an injected SQL executor."""

    def __init__(self, executor: SqlExecutor | None = None) -> None:
        self._executor = executor

    def find_by_capability(
        self, capability: str, *, limit: int = 20
    ) -> FacilityQueryResult:
        if self._executor is None:
            return FacilityQueryResult(
                candidates=(),
                connected=False,
                message="Databricks is not configured; no live facility claims were queried.",
            )
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        rows = self._executor.execute(_FACILITY_QUERY, (capability, limit))
        return FacilityQueryResult(
            candidates=tuple(_translate_row(row) for row in rows),
            connected=True,
            message="Facility candidates loaded from Databricks evidence tables.",
        )

    def find_by_capability_near(
        self,
        capability: str,
        *,
        origin: Sequence[object],
        limit: int = 20,
    ) -> FacilityQueryResult:
        """Return source-backed candidates ordered by straight-line distance.

        The distance is a geodesic estimate between valid coordinates, not a
        road route, travel time, fare, or statement of current availability.
        """

        if self._executor is None:
            return FacilityQueryResult(
                candidates=(),
                connected=False,
                message="Databricks is not configured; no live facility claims were queried.",
            )
        latitude, longitude = validate_coordinates(origin)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        rows = self._executor.execute(
            _NEARBY_FACILITY_QUERY,
            (latitude, latitude, longitude, capability, limit),
        )
        return FacilityQueryResult(
            candidates=tuple(_translate_row(row) for row in rows),
            connected=True,
            message=(
                "Facility candidates loaded from Databricks evidence tables; "
                "distance is a straight-line coordinate estimate."
            ),
        )


class PlanStore(Protocol):
    def save_plan(self, plan: Mapping[str, object]) -> dict[str, object]: ...

    def get_plan(self, plan_id: str) -> dict[str, object] | None: ...

    def save_feedback(
        self, plan_id: str, feedback: Mapping[str, object]
    ) -> dict[str, object]: ...

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]: ...


class SessionLocalPlanStore:
    """Copy-isolated state store backed by a caller-owned session mapping."""

    _PLANS_KEY = "aven_saved_plans"
    _FEEDBACK_KEY = "aven_access_feedback"

    def __init__(self, session_state: MutableMapping[str, object] | None = None) -> None:
        self._state = session_state if session_state is not None else {}
        self._state.setdefault(self._PLANS_KEY, {})
        self._state.setdefault(self._FEEDBACK_KEY, {})

    def _plans(self) -> MutableMapping[str, dict[str, object]]:
        plans = self._state[self._PLANS_KEY]
        if not isinstance(plans, MutableMapping):
            raise TypeError("session plan state must be a mutable mapping")
        return plans

    def _feedback(self) -> MutableMapping[str, list[dict[str, object]]]:
        feedback = self._state[self._FEEDBACK_KEY]
        if not isinstance(feedback, MutableMapping):
            raise TypeError("session feedback state must be a mutable mapping")
        return feedback

    def save_plan(self, plan: Mapping[str, object]) -> dict[str, object]:
        plan_id = _text(plan.get("plan_id"))
        if not plan_id:
            raise ValueError("plan_id is required")
        saved = deepcopy(dict(plan))
        saved["plan_id"] = plan_id
        self._plans()[plan_id] = saved
        return deepcopy(saved)

    def get_plan(self, plan_id: str) -> dict[str, object] | None:
        saved = self._plans().get(_text(plan_id))
        return deepcopy(saved) if saved is not None else None

    def save_feedback(
        self, plan_id: str, feedback: Mapping[str, object]
    ) -> dict[str, object]:
        normalised_plan_id = _text(plan_id)
        if not normalised_plan_id:
            raise ValueError("plan_id is required")
        saved = deepcopy(dict(feedback))
        saved["plan_id"] = normalised_plan_id
        self._feedback().setdefault(normalised_plan_id, []).append(saved)
        return deepcopy(saved)

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]:
        entries = self._feedback().get(_text(plan_id), [])
        return tuple(deepcopy(entry) for entry in entries)


class FallbackPlanStore:
    """Prefer a persistent store, then remain on session state after an outage."""

    def __init__(self, primary: PlanStore, fallback: PlanStore) -> None:
        self._primary = primary
        self._fallback = fallback
        self.using_fallback = False

    def _store(self) -> PlanStore:
        return self._fallback if self.using_fallback else self._primary

    def _run(self, method: str, *args: object) -> object:
        store = self._store()
        try:
            return getattr(store, method)(*args)
        except (ConnectionError, TimeoutError, OSError):
            if store is self._fallback:
                raise
            self.using_fallback = True
            return getattr(self._fallback, method)(*args)

    def save_plan(self, plan: Mapping[str, object]) -> dict[str, object]:
        return self._run("save_plan", plan)  # type: ignore[return-value]

    def get_plan(self, plan_id: str) -> dict[str, object] | None:
        return self._run("get_plan", plan_id)  # type: ignore[return-value]

    def save_feedback(
        self, plan_id: str, feedback: Mapping[str, object]
    ) -> dict[str, object]:
        return self._run("save_feedback", plan_id, feedback)  # type: ignore[return-value]

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]:
        return self._run("list_feedback", plan_id)  # type: ignore[return-value]
