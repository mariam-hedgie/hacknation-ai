"""Security tests for Databricks-proxy identity and local demo isolation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.auth import (  # noqa: E402
    AuthenticationError,
    AuthConfigurationError,
    resolve_identity,
)


class IdentityResolutionTests(unittest.TestCase):
    def test_databricks_mode_requires_authenticated_proxy_identity(self) -> None:
        with self.assertRaises(AuthenticationError):
            resolve_identity(
                {},
                {
                    "AVEN_AUTH_MODE": "databricks",
                    "AVEN_IDENTITY_PEPPER": "p" * 32,
                },
            )

    def test_databricks_identity_is_pseudonymous_and_stable(self) -> None:
        headers = {
            "X-Forwarded-User": "workspace-user-123",
            "X-Forwarded-Preferred-Username": "Mariam",
            "X-Forwarded-Email": "mariam@example.com",
        }
        env = {
            "AVEN_AUTH_MODE": "databricks",
            "AVEN_IDENTITY_PEPPER": "deployment-specific-secret-value",
        }

        first = resolve_identity(headers, env)
        second = resolve_identity(headers, env)

        self.assertEqual(first.owner_id, second.owner_id)
        self.assertEqual(len(first.owner_id), 64)
        self.assertNotIn("workspace-user-123", repr(first))
        self.assertNotIn("mariam@example.com", repr(first))
        self.assertEqual(first.display_name, "Mariam")
        self.assertTrue(first.authenticated)

    def test_identity_header_injection_is_rejected(self) -> None:
        for invalid in ("user-a,user-b", "user-a\nuser-b", "", "x" * 300):
            with self.subTest(invalid=invalid):
                with self.assertRaises(AuthenticationError):
                    resolve_identity(
                        {"X-Forwarded-User": invalid},
                        {
                            "AVEN_AUTH_MODE": "databricks",
                            "AVEN_IDENTITY_PEPPER": "p" * 32,
                        },
                    )

    def test_short_or_missing_identity_pepper_fails_closed(self) -> None:
        for pepper in (None, "too-short"):
            env = {"AVEN_AUTH_MODE": "databricks"}
            if pepper is not None:
                env["AVEN_IDENTITY_PEPPER"] = pepper
            with self.subTest(pepper=pepper):
                with self.assertRaises(AuthConfigurationError):
                    resolve_identity({"X-Forwarded-User": "user-1"}, env)

    def test_local_demo_requires_explicit_opt_in(self) -> None:
        with self.assertRaises(AuthConfigurationError):
            resolve_identity({}, {"AVEN_AUTH_MODE": "local_demo"})

        identity = resolve_identity(
            {},
            {
                "AVEN_AUTH_MODE": "local_demo",
                "AVEN_ALLOW_LOCAL_DEMO": "true",
            },
        )
        self.assertFalse(identity.authenticated)
        self.assertEqual(identity.owner_id, "local-demo")

    def test_local_demo_is_blocked_inside_a_databricks_app(self) -> None:
        with self.assertRaises(AuthConfigurationError):
            resolve_identity(
                {},
                {
                    "AVEN_AUTH_MODE": "local_demo",
                    "AVEN_ALLOW_LOCAL_DEMO": "true",
                    "DATABRICKS_CLIENT_ID": "app-service-principal",
                },
            )

    def test_unknown_or_missing_auth_mode_fails_closed(self) -> None:
        for mode in (None, "password", "off"):
            env = {} if mode is None else {"AVEN_AUTH_MODE": mode}
            with self.subTest(mode=mode):
                with self.assertRaises(AuthConfigurationError):
                    resolve_identity({}, env)


if __name__ == "__main__":
    unittest.main()
