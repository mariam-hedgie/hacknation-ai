"""Backend integration seam for the Aven Referral Copilot.

The frontend talks ONLY to `service` in this package — never directly to a
Databricks tool. Each required tool from the Data Legend brief has its own
import-safe stub here (Mosaic AI Vector Search, Agent Bricks, Genie, MLflow 3
tracing, Lakebase). Every stub degrades to the existing deterministic demo /
local behavior when the tool is not configured, so the app runs unchanged
locally and lights up as each integration is filled in.

See apps/TODO.md for exactly what to implement per tool.
"""

from . import service

__all__ = ["service"]
