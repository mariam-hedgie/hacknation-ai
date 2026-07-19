"""Databricks Apps entry point for the React + FastAPI production surface."""

from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "src.backend.api:app",
        host="0.0.0.0",
        port=int(os.getenv("DATABRICKS_APP_PORT", "8010")),
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1",
    )
