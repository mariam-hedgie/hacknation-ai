"""Guards the governed-copy boundary described in src/localization.py.

Governed copy is the wording that changes what a user believes about a hospital
or an emergency. It must be translated for every supported language and must
never be hardcoded in a view, where it would silently render in English.
"""

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.domain import EvidenceStatus
from src.localization import (
    EVIDENCE_STATUS_KEYS,
    SAFETY_CRITICAL,
    SUPPORTED_LANGUAGES,
    TRUST_LEVEL_KEYS,
    _COPY,
    translate_core,
)
from src.trust import TrustLevel

# Views that must not carry governed copy of their own.
VIEW_FILES = ("app.py", "src/styles.py")


class GovernedCopyCoverageTests(unittest.TestCase):
    def test_every_governed_key_exists_in_every_language(self):
        for key, table in _COPY.items():
            for code in SUPPORTED_LANGUAGES:
                with self.subTest(key=key, language=code):
                    self.assertIn(code, table, f"{key} has no {code} translation")
                    self.assertTrue(table[code].strip(), f"{key}/{code} is blank")

    def test_translations_are_not_english_copies(self):
        """A pasted English string is an untranslated string wearing a label."""
        for key, table in _COPY.items():
            for code in SUPPORTED_LANGUAGES:
                if code == "en":
                    continue
                with self.subTest(key=key, language=code):
                    self.assertNotEqual(
                        table[code].strip(),
                        table["en"].strip(),
                        f"{key}/{code} is identical to the English string",
                    )

    def test_unknown_keys_raise_instead_of_degrading(self):
        with self.assertRaises(KeyError):
            translate_core("no_such_key", "en")


class StatusMappingTests(unittest.TestCase):
    """Every domain state must resolve to approved wording, or a view will
    invent its own and the badge/receipt copy will drift apart."""

    def test_every_trust_level_maps_to_an_approved_key(self):
        for level in TrustLevel:
            with self.subTest(level=level.value):
                self.assertIn(level.value, TRUST_LEVEL_KEYS)
                self.assertIn(TRUST_LEVEL_KEYS[level.value], _COPY)

    def test_every_evidence_status_maps_to_an_approved_key(self):
        for status in EvidenceStatus:
            with self.subTest(status=status.value):
                self.assertIn(status.value, EVIDENCE_STATUS_KEYS)
                self.assertIn(EVIDENCE_STATUS_KEYS[status.value], _COPY)

    def test_ui_only_statuses_are_covered_too(self):
        for status in ("external_corroborated", "user_context"):
            with self.subTest(status=status):
                self.assertIn(EVIDENCE_STATUS_KEYS[status], _COPY)


class NoHardcodedGovernedCopyTests(unittest.TestCase):
    def test_safety_critical_keys_are_all_real_keys(self):
        self.assertEqual(SAFETY_CRITICAL - set(_COPY), set())

    def test_views_do_not_hardcode_safety_critical_strings(self):
        for relative in VIEW_FILES:
            source = (APP_ROOT / relative).read_text(encoding="utf-8")
            for key in sorted(SAFETY_CRITICAL):
                with self.subTest(file=relative, key=key):
                    self.assertNotIn(
                        _COPY[key]["en"],
                        source,
                        f"{relative} hardcodes the safety-critical string {key!r}; "
                        "use safety_copy(key) so it translates.",
                    )

    def test_the_evidence_and_trust_vocabularies_are_all_safety_critical(self):
        """Badge and receipt wording is exactly what must not drift into a view."""
        for key in set(TRUST_LEVEL_KEYS.values()) | set(EVIDENCE_STATUS_KEYS.values()):
            with self.subTest(key=key):
                self.assertIn(key, SAFETY_CRITICAL)


if __name__ == "__main__":
    unittest.main()
