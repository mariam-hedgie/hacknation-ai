"""Durable PlanStore implementation for a Lakebase/PostgreSQL boundary.

The executor is injected so the Databricks App can use its managed database
resource and service identity.  SQL identifiers are validated and every user
value is passed as a bound parameter.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Mapping, Protocol, Sequence


_IDENTIFIER = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}$"
)
_MAX_PAYLOAD_BYTES = 64_000


class PersistenceExecutor(Protocol):
    """Execute controlled SQL with psycopg-style bound parameters."""

    def execute(
        self, statement: str, parameters: tuple[object, ...]
    ) -> Sequence[Mapping[str, object]]: ...


def _required(value: object, field: str) -> str:
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        raise ValueError(f"{field} is required")
    return cleaned


def _table(value: str, field: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{field} must be a simple SQL identifier")
    return value


def _decode_mapping(value: object, field: str) -> dict[str, object]:
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, Mapping):
        raise ValueError(f"Stored {field} payload must be an object")
    return deepcopy(dict(parsed))


def _encode_mapping(value: Mapping[str, object], field: str) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(encoded.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise ValueError(f"{field} payload exceeds {_MAX_PAYLOAD_BYTES} bytes")
    return encoded


class PersistentSqlPlanStore:
    """Persist plans and append-only access feedback beyond one app session."""

    def __init__(
        self,
        executor: PersistenceExecutor,
        *,
        plans_table: str = "saved_care_plans",
        feedback_table: str = "access_feedback",
    ) -> None:
        self._executor = executor
        self.plans_table = _table(plans_table, "plans_table")
        self.feedback_table = _table(feedback_table, "feedback_table")

    def save_plan(self, plan: Mapping[str, object]) -> dict[str, object]:
        saved = deepcopy(dict(plan))
        plan_id = _required(saved.get("plan_id"), "plan_id")
        saved["plan_id"] = plan_id
        statement = f"""
INSERT INTO {self.plans_table} (plan_id, payload)
VALUES (%s, %s)
ON CONFLICT (plan_id) DO UPDATE SET
    payload = EXCLUDED.payload,
    updated_at = CURRENT_TIMESTAMP
""".strip()
        self._executor.execute(
            statement,
            (plan_id, _encode_mapping(saved, "plan")),
        )
        return deepcopy(saved)

    def get_plan(self, plan_id: str) -> dict[str, object] | None:
        normalised = _required(plan_id, "plan_id")
        rows = self._executor.execute(
            f"SELECT payload FROM {self.plans_table} WHERE plan_id = %s",
            (normalised,),
        )
        if not rows:
            return None
        return _decode_mapping(rows[0].get("payload"), "plan")

    def save_feedback(
        self, plan_id: str, feedback: Mapping[str, object]
    ) -> dict[str, object]:
        normalised = _required(plan_id, "plan_id")
        saved = deepcopy(dict(feedback))
        saved["plan_id"] = normalised
        self._executor.execute(
            f"INSERT INTO {self.feedback_table} (plan_id, feedback_payload) VALUES (%s, %s)",
            (
                normalised,
                _encode_mapping(saved, "feedback"),
            ),
        )
        return deepcopy(saved)

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]:
        normalised = _required(plan_id, "plan_id")
        rows = self._executor.execute(
            f"""
SELECT feedback_payload
FROM {self.feedback_table}
WHERE plan_id = %s
ORDER BY created_at, feedback_id
""".strip(),
            (normalised,),
        )
        return tuple(
            _decode_mapping(row.get("feedback_payload"), "feedback") for row in rows
        )
