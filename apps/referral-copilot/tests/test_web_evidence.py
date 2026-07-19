"""Tests for privacy-safe, attributable public-source discovery."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.web_evidence import (  # noqa: E402
    WebEvidenceConfigurationError,
    build_facility_query,
    normalize_search_results,
)


class WebEvidenceTests(unittest.TestCase):
    def test_query_uses_only_facility_and_confirmed_capability(self) -> None:
        query = build_facility_query("Patna Heart Centre", "cardiology")

        self.assertEqual(
            query,
            '"Patna Heart Centre" cardiology official contact fees doctors',
        )
        self.assertNotIn("patient", query.casefold())

    def test_blank_facility_or_capability_is_rejected(self) -> None:
        with self.assertRaises(WebEvidenceConfigurationError):
            build_facility_query("", "cardiology")
        with self.assertRaises(WebEvidenceConfigurationError):
            build_facility_query("Hospital", "")

    def test_results_are_attributable_candidates_not_verified_claims(self) -> None:
        rows = normalize_search_results(
            {
                "results": [
                    {
                        "title": "Official facility page",
                        "url": "https://hospital.example/services",
                        "content": "Cardiology contact information.",
                    }
                ]
            },
            retrieved_at="2026-07-19T10:00:00Z",
        )

        self.assertEqual(rows[0].status, "external_source_candidate")
        self.assertEqual(rows[0].retrieved_at, "2026-07-19T10:00:00Z")
        self.assertTrue(rows[0].url.startswith("https://"))

    def test_non_http_results_and_script_urls_are_discarded(self) -> None:
        rows = normalize_search_results(
            {
                "results": [
                    {"title": "Bad", "url": "javascript:alert(1)", "content": "x"},
                    {"title": "Local", "url": "file:///tmp/x", "content": "x"},
                ]
            },
            retrieved_at="2026-07-19T10:00:00Z",
        )

        self.assertEqual(rows, ())

    def test_urls_with_whitespace_or_credentials_are_discarded(self) -> None:
        rows = normalize_search_results(
            {
                "results": [
                    {"title": "Bad", "url": "https://good.example/a bad", "content": "x"},
                    {"title": "Bad", "url": "https://user:pass@good.example/x", "content": "x"},
                ]
            },
            retrieved_at="2026-07-19T10:00:00Z",
        )

        self.assertEqual(rows, ())


if __name__ == "__main__":
    unittest.main()
