"""Owner-scoped, data-minimized persistence for Lakebase/PostgreSQL.

The executor is injected so a Databricks App can use its managed database
resource and service identity. Every operation is scoped to a pseudonymous
owner ID and every user value is passed as a bound parameter.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from copy import deepcopy
from typing import Mapping, Protocol, Sequence


_IDENTIFIER = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}$"
)
_OWNER_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_PLAN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_MAX_PAYLOAD_BYTES = 64_000
_MAX_NOTE_LENGTH = 500
_SENSITIVE_KEYS = frozenset(
    {
        "audio",
        "confirmed_request",
        "demo_user_id",
        "email",
        "home_address",
        "language_preference",
        "location",
        "medication_name",
        "original_text",
        "owner_id",
        "phone",
        "request",
        "transcript",
        "user_id",
        "voice_audio",
    }
)
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


def _validated_owner(value: object) -> str:
    owner_id = _required(value, "owner_id")
    if not _OWNER_ID.fullmatch(owner_id):
        raise ValueError("owner_id must be a bounded pseudonymous identifier")
    return owner_id


def _validated_plan_id(value: object) -> str:
    plan_id = _required(value, "plan_id")
    if not _PLAN_ID.fullmatch(plan_id):
        raise ValueError("plan_id contains unsupported characters or is too long")
    return plan_id


def _table(value: str, field: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{field} must be a simple SQL identifier")
    return value


def _plain_text(value: object, field: str, max_length: int) -> str:
    text = str(value or "").strip()
    if len(text) > max_length:
        raise ValueError(f"{field} exceeds {max_length} characters")
    if any(unicodedata.category(character).startswith("C") for character in text):
        raise ValueError(f"{field} contains unsupported control characters")
    return text


def _decode_mapping(value: object, field: str) -> dict[str, object]:
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, Mapping):
        raise ValueError(f"Stored {field} payload must be an object")
    return deepcopy(dict(parsed))


def _encode_mapping(value: Mapping[str, object], field: str) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} payload contains an unsupported value") from exc
    if len(encoded.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise ValueError(f"{field} payload exceeds {_MAX_PAYLOAD_BYTES} bytes")
    return encoded


def _safe_persistable(value: object, field: str, *, depth: int = 0) -> object:
    """Copy bounded JSON while dropping identity and health-intake keys."""

    if depth > 5:
        raise ValueError(f"{field} is nested too deeply")
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{field} contains a non-finite number")
        return value
    if isinstance(value, str):
        return _plain_text(value, field, 2_000)
    if isinstance(value, Mapping):
        if len(value) > 50:
            raise ValueError(f"{field} contains too many fields")
        safe: dict[str, object] = {}
        for raw_key, item in value.items():
            key = _plain_text(raw_key, f"{field} key", 100)
            if key.casefold() in _SENSITIVE_KEYS:
                continue
            safe[key] = _safe_persistable(item, f"{field}.{key}", depth=depth + 1)
        return safe
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) > 50:
            raise ValueError(f"{field} contains too many items")
        return [
            _safe_persistable(item, f"{field} item", depth=depth + 1)
            for item in value
        ]
    raise ValueError(f"{field} contains an unsupported value")


def _minimise_plan(plan: Mapping[str, object]) -> dict[str, object]:
    """Retain the saved decision, never the conversational health intake."""

    saved: dict[str, object] = {"plan_id": _validated_plan_id(plan.get("plan_id"))}
    facility_id = plan.get("selected_facility_id")
    if facility_id is not None:
        saved["selected_facility_id"] = _plain_text(
            facility_id, "selected_facility_id", 256
        )
    selected_option = plan.get("selected_option")
    if selected_option is not None:
        if not isinstance(selected_option, Mapping):
            raise ValueError("selected_option must be an object")
        saved["selected_option"] = _safe_persistable(
            selected_option, "selected_option"
        )
    next_steps = plan.get("next_steps")
    if next_steps is not None:
        if isinstance(next_steps, (str, bytes)) or not isinstance(next_steps, Sequence):
            raise ValueError("next_steps must be a list")
        if len(next_steps) > 10:
            raise ValueError("next_steps may contain at most 10 items")
        saved["next_steps"] = [
            _plain_text(item, "next_step", 500) for item in next_steps
        ]
    user_override = plan.get("user_override")
    if user_override is not None:
        if not isinstance(user_override, Mapping):
            raise ValueError("user_override must be an object")
        saved["user_override"] = {
            "facility_id": _plain_text(
                user_override.get("facility_id"), "override facility_id", 256
            ),
            "note": _plain_text(
                user_override.get("note"), "override note", _MAX_NOTE_LENGTH
            ),
            "selected_despite_rank": bool(
                user_override.get("selected_despite_rank", True)
            ),
        }
    _encode_mapping(saved, "plan")
    return saved


def _minimise_feedback(plan_id: str, feedback: Mapping[str, object]) -> dict[str, object]:
    status = _plain_text(feedback.get("status"), "feedback status", 40).casefold()
    if status not in _FEEDBACK_STATUSES:
        raise ValueError("Choose one of Aven's bounded feedback statuses.")
    saved = {
        "plan_id": plan_id,
        "status": status,
        "note": _plain_text(feedback.get("note"), "feedback note", _MAX_NOTE_LENGTH),
    }
    _encode_mapping(saved, "feedback")
    return saved


class PersistentSqlPlanStore:
    """Persist only one authenticated owner's minimized decisions and feedback."""

    def __init__(
        self,
        executor: PersistenceExecutor,
        *,
        owner_id: str,
        plans_table: str = "saved_care_plans",
        feedback_table: str = "access_feedback",
    ) -> None:
        self._executor = executor
        self._owner_id = _validated_owner(owner_id)
        self.plans_table = _table(plans_table, "plans_table")
        self.feedback_table = _table(feedback_table, "feedback_table")

    def save_plan(self, plan: Mapping[str, object]) -> dict[str, object]:
        saved = _minimise_plan(plan)
        plan_id = str(saved["plan_id"])
        statement = f"""
INSERT INTO {self.plans_table} (owner_id, plan_id, payload)
VALUES (%s, %s, %s)
ON CONFLICT (owner_id, plan_id) DO UPDATE SET
    payload = EXCLUDED.payload,
    updated_at = CURRENT_TIMESTAMP,
    expires_at = CURRENT_TIMESTAMP + INTERVAL '30 days'
""".strip()
        self._executor.execute(
            statement,
            (self._owner_id, plan_id, _encode_mapping(saved, "plan")),
        )
        return deepcopy(saved)

    def get_plan(self, plan_id: str) -> dict[str, object] | None:
        normalised = _validated_plan_id(plan_id)
        rows = self._executor.execute(
            f"""
SELECT payload
FROM {self.plans_table}
WHERE owner_id = %s AND plan_id = %s AND expires_at > CURRENT_TIMESTAMP
""".strip(),
            (self._owner_id, normalised),
        )
        if not rows:
            return None
        return _decode_mapping(rows[0].get("payload"), "plan")

    def list_plans(self) -> tuple[dict[str, object], ...]:
        """List only this owner's unexpired plans, newest first."""

        rows = self._executor.execute(
            f"""
SELECT payload
FROM {self.plans_table}
WHERE owner_id = %s AND expires_at > CURRENT_TIMESTAMP
ORDER BY updated_at DESC, plan_id
""".strip(),
            (self._owner_id,),
        )
        return tuple(_decode_mapping(row.get("payload"), "plan") for row in rows)

    def save_feedback(
        self, plan_id: str, feedback: Mapping[str, object]
    ) -> dict[str, object]:
        normalised = _validated_plan_id(plan_id)
        saved = _minimise_feedback(normalised, feedback)
        rows = self._executor.execute(
            f"""
INSERT INTO {self.feedback_table} (owner_id, plan_id, feedback_payload)
SELECT %s, %s, %s
FROM {self.plans_table}
WHERE owner_id = %s AND plan_id = %s AND expires_at > CURRENT_TIMESTAMP
RETURNING feedback_id
""".strip(),
            (
                self._owner_id,
                normalised,
                _encode_mapping(saved, "feedback"),
                self._owner_id,
                normalised,
            ),
        )
        if not rows:
            raise KeyError("Plan not found for the signed-in user.")
        return deepcopy(saved)

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]:
        normalised = _validated_plan_id(plan_id)
        rows = self._executor.execute(
            f"""
SELECT feedback_payload
FROM {self.feedback_table}
WHERE owner_id = %s AND plan_id = %s
ORDER BY created_at, feedback_id
""".strip(),
            (self._owner_id, normalised),
        )
        return tuple(
            _decode_mapping(row.get("feedback_payload"), "feedback") for row in rows
        )

    def delete_plan(self, plan_id: str) -> bool:
        """Delete this owner's plan; the schema cascades its feedback rows."""

        normalised = _validated_plan_id(plan_id)
        rows = self._executor.execute(
            f"""
DELETE FROM {self.plans_table}
WHERE owner_id = %s AND plan_id = %s
RETURNING plan_id
""".strip(),
            (self._owner_id, normalised),
        )
        return bool(rows)

    def purge_expired(self) -> int:
        """Delete expired plans for all owners; feedback cascades in Lakebase."""

        rows = self._executor.execute(
            f"""
DELETE FROM {self.plans_table}
WHERE expires_at <= CURRENT_TIMESTAMP
RETURNING plan_id
""".strip(),
            (),
        )
        return len(rows)
