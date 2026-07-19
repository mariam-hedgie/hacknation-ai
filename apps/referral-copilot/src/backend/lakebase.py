"""Managed Lakebase runtime for authenticated, owner-scoped saved decisions.

Databricks Apps inject PostgreSQL coordinates for the attached Lakebase
resource. A fresh short-lived OAuth database credential is generated for each
connection, so no database password is stored in source or browser state.
"""

from __future__ import annotations

import os
import threading
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .. import profiles as local_profiles
from ..auth import UserIdentity, resolve_identity
from ..databricks_adapter import SessionLocalPlanStore
from ..persistence import PersistentSqlPlanStore, _minimise_feedback, _minimise_plan
from .config import BackendConfig


_REQUIRED_DATABASE_ENV = ("PGHOST", "PGDATABASE", "PGUSER", "ENDPOINT_NAME")

# Local-demo scratch state, keyed by opaque browser session. A single shared
# dict would let every visitor to a public demo host read and delete every
# other visitor's saved plans, so each session gets its own isolated mapping.
# Bounded because this is process memory on a long-lived host; the oldest
# session is evicted once the cap is reached.
_LOCAL_SESSION_CAP = 500
_LOCAL_SESSIONS: "OrderedDict[str, dict[str, object]]" = OrderedDict()
_LOCAL_SESSIONS_LOCK = threading.Lock()
_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY = False


def _local_session_state(session_key: str) -> dict[str, object]:
    """Return the isolated scratch mapping for one local-demo session."""

    key = str(session_key or "").strip() or "anonymous"
    with _LOCAL_SESSIONS_LOCK:
        state = _LOCAL_SESSIONS.get(key)
        if state is None:
            state = {}
            _LOCAL_SESSIONS[key] = state
            while len(_LOCAL_SESSIONS) > _LOCAL_SESSION_CAP:
                _LOCAL_SESSIONS.popitem(last=False)
        else:
            _LOCAL_SESSIONS.move_to_end(key)
        return state


def _configured_database(environ: Mapping[str, str]) -> bool:
    return all(str(environ.get(name, "")).strip() for name in _REQUIRED_DATABASE_ENV)


class LakebasePostgresExecutor:
    """Execute parameterized PostgreSQL statements with rotating OAuth tokens."""

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        credential_provider: Callable[[str], str] | None = None,
        connect: Callable[..., object] | None = None,
    ) -> None:
        self._env = os.environ if environ is None else environ
        missing = [name for name in _REQUIRED_DATABASE_ENV if not str(self._env.get(name, "")).strip()]
        if missing:
            raise RuntimeError("Lakebase is not fully configured for this app.")

        if credential_provider is None:
            from databricks.sdk import WorkspaceClient

            workspace = WorkspaceClient()

            def credential_provider(endpoint: str) -> str:
                return str(workspace.postgres.generate_database_credential(endpoint=endpoint).token)

        if connect is None:
            import psycopg

            connect = psycopg.connect
        self._credential_provider = credential_provider
        self._connect = connect

    def execute(
        self, statement: str, parameters: tuple[object, ...]
    ) -> Sequence[Mapping[str, object]]:
        endpoint = str(self._env["ENDPOINT_NAME"])
        password = self._credential_provider(endpoint)
        with self._connect(
            host=str(self._env["PGHOST"]),
            dbname=str(self._env["PGDATABASE"]),
            user=str(self._env["PGUSER"]),
            port=str(self._env.get("PGPORT", "5432")),
            sslmode=str(self._env.get("PGSSLMODE", "require")),
            password=password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, parameters)
                if cursor.description is None:
                    return ()
                names = []
                for column in cursor.description:
                    name = getattr(column, "name", None)
                    names.append(str(name if name is not None else column[0]))
                return tuple(dict(zip(names, row, strict=True)) for row in cursor.fetchall())

    def ensure_schema(self) -> None:
        """Create the owner-scoped tables as the App service principal."""

        checks = self.execute(
            """
SELECT
  to_regclass('saved_care_plans') IS NOT NULL AS plans_exist,
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'saved_care_plans' AND column_name = 'owner_id'
  ) AS plans_have_owner,
  to_regclass('access_feedback') IS NOT NULL AS feedback_exists,
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'access_feedback' AND column_name = 'owner_id'
  ) AS feedback_has_owner
""".strip(),
            (),
        )
        state = checks[0] if checks else {}
        if (state.get("plans_exist") and not state.get("plans_have_owner")) or (
            state.get("feedback_exists") and not state.get("feedback_has_owner")
        ):
            raise RuntimeError("Unsafe legacy Lakebase schema detected; owner_id is required.")

        self.execute(
            """
CREATE TABLE IF NOT EXISTS saved_care_plans (
  owner_id TEXT NOT NULL CHECK (owner_id ~ '^[A-Za-z0-9_-]{1,128}$'),
  plan_id TEXT NOT NULL CHECK (plan_id ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'),
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
  PRIMARY KEY (owner_id, plan_id)
)
""".strip(),
            (),
        )
        self.execute(
            """
CREATE TABLE IF NOT EXISTS access_feedback (
  feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  owner_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  feedback_payload JSONB NOT NULL CHECK (jsonb_typeof(feedback_payload) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (owner_id, plan_id)
    REFERENCES saved_care_plans (owner_id, plan_id) ON DELETE CASCADE,
  CHECK (feedback_payload ->> 'status' IN (
    'helpful', 'needs_correction', 'not_sure', 'service_unavailable',
    'price_differed', 'accepted', 'not_visited'
  )),
  CHECK (length(COALESCE(feedback_payload ->> 'note', '')) <= 500)
)
""".strip(),
            (),
        )
        self.execute(
            "CREATE INDEX IF NOT EXISTS saved_care_plans_owner_updated_idx ON saved_care_plans (owner_id, updated_at DESC)",
            (),
        )
        self.execute(
            "CREATE INDEX IF NOT EXISTS access_feedback_owned_plan_idx ON access_feedback (owner_id, plan_id, created_at, feedback_id)",
            (),
        )


class LocalDemoPlanStore:
    """Process-local, minimized fallback used only in explicit local-demo mode.

    Scoped to one browser session so visitors to a shared demo host stay
    isolated from each other. Still process-local: a restart clears everything.
    """

    def __init__(self, session_key: str = "") -> None:
        self._store = SessionLocalPlanStore(_local_session_state(session_key))

    def save_plan(self, plan: Mapping[str, object]) -> dict[str, object]:
        return self._store.save_plan(_minimise_plan(plan))

    def get_plan(self, plan_id: str) -> dict[str, object] | None:
        return self._store.get_plan(plan_id)

    def list_plans(self) -> tuple[dict[str, object], ...]:
        return self._store.list_plans()

    def save_feedback(self, plan_id: str, feedback: Mapping[str, object]) -> dict[str, object]:
        if self.get_plan(plan_id) is None:
            raise KeyError("Plan not found for the local demo.")
        return self._store.save_feedback(plan_id, _minimise_feedback(plan_id, feedback))

    def list_feedback(self, plan_id: str) -> tuple[dict[str, object], ...]:
        return self._store.list_feedback(plan_id)

    def delete_plan(self, plan_id: str) -> bool:
        return self._store.delete_plan(plan_id)


def plan_store_for_headers(
    headers: Mapping[str, str],
    environ: Mapping[str, str] | None = None,
    session_key: str = "",
) -> tuple[UserIdentity, PersistentSqlPlanStore | LocalDemoPlanStore]:
    """Resolve server-trusted identity and return its correctly scoped store.

    `session_key` is an opaque, server-issued browser session used only to keep
    local-demo visitors isolated. It is never an identity: authenticated
    Databricks owners are always scoped by `owner_id` instead.
    """

    env = os.environ if environ is None else environ
    identity = resolve_identity(headers, env)
    if identity.auth_source == "local_demo":
        return identity, LocalDemoPlanStore(session_key)
    if not _configured_database(env):
        raise RuntimeError("Lakebase persistence is required but not configured.")
    executor = LakebasePostgresExecutor(environ=env)
    store = PersistentSqlPlanStore(executor, owner_id=identity.owner_id)
    global _SCHEMA_READY
    if not _SCHEMA_READY:
        with _SCHEMA_LOCK:
            if not _SCHEMA_READY:
                executor.ensure_schema()
                # Enforce the documented retention window on safe app startup;
                # the owner-scoped foreign key cascades expired feedback.
                store.purge_expired()
                _SCHEMA_READY = True
    return identity, store


class LakebasePersistence:
    """Legacy local-profile adapter retained for the Streamlit fallback only."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        return self._config.has_lakebase

    def load_profile(self, email: str) -> dict[str, Any]:
        return local_profiles.load_profile(email)

    def save_profile(self, profile: dict[str, Any]) -> None:
        local_profiles.save_profile(profile)
