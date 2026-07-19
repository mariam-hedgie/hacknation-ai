"""Non-secret backend configuration, read from the environment.

Databricks Apps inject resource coordinates as environment variables. Every
field is optional: when a tool's coordinates are absent (or still a `TODO_...`
placeholder from .env.example), that tool reports itself unavailable and the
service falls back to demo/local behavior. Secrets (tokens) are NOT read here —
the Databricks App identity authorizes live calls.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:  # pragma: no cover - optional local-dev convenience
    from dotenv import load_dotenv

    # A Databricks App injects env vars directly and has no .env file, so this
    # is a no-op there. Locally, nothing else in this app ever loads .env
    # (deliberately: Databricks Apps must not depend on one) — this is the one
    # place that does, since every entry point (app.py, api.py, the standalone
    # scripts) imports this module before touching any env-derived config.
    load_dotenv(Path(__file__).resolve().parents[4] / ".env")
except ImportError:
    pass


def _clean(value: str | None) -> str:
    """Return a usable value, or "" for blank / `TODO_...` placeholders."""
    text = (value or "").strip()
    if not text or text.upper().startswith("TODO"):
        return ""
    return text


@dataclass(frozen=True)
class BackendConfig:
    # Databricks SQL warehouse (facility evidence tables)
    server_hostname: str = ""
    http_path: str = ""
    catalog: str = ""
    schema: str = ""
    # Mosaic AI Vector Search (retrieval across the 10k rows)
    vector_search_endpoint: str = ""
    vector_search_index: str = ""
    # Agent Bricks / Foundation Model serving (extraction + trust scoring)
    serving_endpoint: str = ""
    # Genie (autonomous, multi-step data tasks)
    genie_space_id: str = ""
    # Lakebase Autoscaling resource (managed Postgres coordinates)
    lakebase_endpoint: str = ""
    lakebase_host: str = ""
    lakebase_database: str = ""
    lakebase_user: str = ""
    # MLflow 3 (agent observability + trace cost tracking)
    mlflow_experiment: str = ""

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "BackendConfig":
        env = os.environ if environ is None else environ
        g = lambda k: _clean(env.get(k))  # noqa: E731
        return cls(
            server_hostname=g("DATABRICKS_SERVER_HOSTNAME"),
            http_path=g("DATABRICKS_HTTP_PATH"),
            catalog=g("AVEN_CATALOG"),
            schema=g("AVEN_SCHEMA"),
            vector_search_endpoint=g("AVEN_VECTOR_SEARCH_ENDPOINT"),
            vector_search_index=g("AVEN_VECTOR_SEARCH_INDEX"),
            serving_endpoint=g("AVEN_SERVING_ENDPOINT"),
            genie_space_id=g("AVEN_GENIE_SPACE_ID"),
            lakebase_endpoint=g("ENDPOINT_NAME"),
            lakebase_host=g("PGHOST"),
            lakebase_database=g("PGDATABASE"),
            lakebase_user=g("PGUSER"),
            mlflow_experiment=g("AVEN_MLFLOW_EXPERIMENT"),
        )

    @property
    def has_sql(self) -> bool:
        return bool(self.server_hostname and self.http_path)

    @property
    def has_vector_search(self) -> bool:
        return bool(self.vector_search_endpoint and self.vector_search_index)

    @property
    def has_agent(self) -> bool:
        return bool(self.serving_endpoint)

    @property
    def has_genie(self) -> bool:
        return bool(self.genie_space_id)

    @property
    def has_lakebase(self) -> bool:
        return bool(
            self.lakebase_endpoint
            and self.lakebase_host
            and self.lakebase_database
            and self.lakebase_user
        )

    @property
    def has_mlflow(self) -> bool:
        return bool(self.mlflow_experiment)

    def mode(self) -> str:
        """"live" once authenticated evidence retrieval is configured.

        The active validator is deterministic and does not call a model-serving
        endpoint, so requiring one would incorrectly label real Vector Search
        results as demo data.
        """
        return "live" if self.has_vector_search else "demo"
