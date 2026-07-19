"""Contract tests for the MLflow tracing seam (src/backend/tracing.py)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend import tracing  # noqa: E402


class SpanNoopTests(unittest.TestCase):
    """MLflow is not installed/configured in this environment, so every span
    must be a safe no-op: never raise, never require the caller to guard."""

    def test_span_yields_a_handle_that_accepts_inputs_and_outputs(self) -> None:
        with tracing.span("test.span", inputs={"a": 1}, extra="attr") as handle:
            handle.set_outputs({"b": 2})
            handle.set_attributes({"c": 3})
        # Reaching here without raising is the assertion.

    def test_traced_decorator_still_calls_the_wrapped_function(self) -> None:
        @tracing.traced("test.traced")
        def add(a: int, b: int) -> int:
            return a + b

        self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
