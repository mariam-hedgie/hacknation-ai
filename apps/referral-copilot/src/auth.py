"""Fail-closed identity boundary for Aven's Databricks App deployment.

Databricks performs the interactive OAuth login.  Aven accepts the resulting
proxy identity only when explicitly configured for Databricks mode, converts it
to an app-scoped pseudonymous owner ID, and never stores the raw user ID/email.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import unicodedata
from dataclasses import dataclass
from typing import Mapping


class AuthenticationError(PermissionError):
    """Raised when a request has no valid authenticated Databricks identity."""


class AuthConfigurationError(RuntimeError):
    """Raised when authentication configuration would fail open."""


@dataclass(frozen=True)
class UserIdentity:
    owner_id: str
    display_name: str
    authenticated: bool
    auth_source: str


def _header(headers: Mapping[str, str], name: str) -> str:
    wanted = name.casefold()
    for key, value in headers.items():
        if str(key).casefold() == wanted:
            return str(value).strip()
    return ""


def _clean_header(value: str, *, label: str, max_length: int) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > max_length or "," in cleaned:
        raise AuthenticationError(f"Invalid {label} from the authenticated proxy.")
    if any(unicodedata.category(character).startswith("C") for character in cleaned):
        raise AuthenticationError(f"Invalid {label} from the authenticated proxy.")
    return cleaned


def _display_name(headers: Mapping[str, str]) -> str:
    value = _header(headers, "X-Forwarded-Preferred-Username")
    if not value:
        return "Signed-in user"
    try:
        return _clean_header(value, label="display name", max_length=100)
    except AuthenticationError:
        return "Signed-in user"


def resolve_identity(
    headers: Mapping[str, str],
    environ: Mapping[str, str] | None = None,
) -> UserIdentity:
    """Resolve an owner without accepting an app-supplied user ID.

    `X-Forwarded-User` is trusted only in explicit Databricks mode, where the
    Databricks reverse proxy is the authentication boundary.  Local demo mode
    is deliberately anonymous, isolated, and blocked when deployment markers
    are present.
    """

    env = os.environ if environ is None else environ
    mode = str(env.get("AVEN_AUTH_MODE", "")).strip().casefold()
    if mode == "databricks":
        subject = _clean_header(
            _header(headers, "X-Forwarded-User"),
            label="user identity",
            max_length=256,
        )
        pepper = str(env.get("AVEN_IDENTITY_PEPPER", ""))
        if len(pepper.encode("utf-8")) < 32:
            raise AuthConfigurationError(
                "AVEN_IDENTITY_PEPPER must be a Databricks secret of at least 32 bytes."
            )
        owner_id = hmac.new(
            pepper.encode("utf-8"),
            subject.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return UserIdentity(
            owner_id=owner_id,
            display_name=_display_name(headers),
            authenticated=True,
            auth_source="databricks_oauth_proxy",
        )

    if mode == "local_demo":
        if str(env.get("AVEN_ALLOW_LOCAL_DEMO", "")).casefold() != "true":
            raise AuthConfigurationError(
                "Local demo identity requires AVEN_ALLOW_LOCAL_DEMO=true."
            )
        deployment_markers = (
            "DATABRICKS_CLIENT_ID",
            "DATABRICKS_APP_NAME",
            "PGAPPNAME",
        )
        if any(str(env.get(name, "")).strip() for name in deployment_markers):
            raise AuthConfigurationError(
                "Anonymous local demo identity is forbidden in a Databricks deployment."
            )
        return UserIdentity(
            owner_id="local-demo",
            display_name="Local demo",
            authenticated=False,
            auth_source="local_demo",
        )

    raise AuthConfigurationError(
        "AVEN_AUTH_MODE must be explicitly set to databricks or local_demo."
    )
