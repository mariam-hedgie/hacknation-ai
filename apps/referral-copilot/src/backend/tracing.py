"""MLflow 3 tracing seam (observability + trace cost tracking).

`span()` is a context manager and `traced()` a decorator. Both are no-ops until
MLflow is installed and an experiment is configured, so importing this module
never requires the mlflow package to be present. Once wired, every step of the
evidence pipeline (retrieve -> extract -> score -> rank) should run inside a
span so the demo can show the reasoning trace the brief's stretch goal asks for.
"""

from __future__ import annotations

import contextlib
from typing import Any, Callable, Iterator

from .config import BackendConfig

_CONFIG = BackendConfig.from_env()

# Lazily resolved mlflow module (or None if unavailable). Guarded so local runs
# without mlflow installed keep working.
_mlflow: Any = None
_resolved = False


def _get_mlflow() -> Any:
    global _mlflow, _resolved
    if _resolved:
        return _mlflow
    _resolved = True
    if not _CONFIG.has_mlflow:
        _mlflow = None
        return None
    try:  # pragma: no cover - depends on deploy environment
        import mlflow  # type: ignore

        mlflow.set_experiment(_CONFIG.mlflow_experiment)
        _mlflow = mlflow
    except Exception:
        # Not installed / not authorized: stay a no-op.
        _mlflow = None
    return _mlflow


class SpanHandle:
    """Uniform, exception-safe interface over an active MLflow span or a no-op.

    Every method is a no-op when MLflow is unavailable (or a call fails), so
    call sites never need to guard on `backend_mode()` or wrap in try/except
    themselves — the reasoning trace is best-effort, never load-bearing.
    """

    def __init__(self, active: Any = None) -> None:
        self._active = active

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        if self._active is None or not attributes:
            return
        try:  # pragma: no cover - depends on deploy environment
            self._active.set_attributes(attributes)
        except Exception:
            pass

    def set_inputs(self, inputs: Any) -> None:
        if self._active is None:
            return
        try:  # pragma: no cover - depends on deploy environment
            self._active.set_inputs(inputs)
        except Exception:
            pass

    def set_outputs(self, outputs: Any) -> None:
        if self._active is None:
            return
        try:  # pragma: no cover - depends on deploy environment
            self._active.set_outputs(outputs)
        except Exception:
            pass


@contextlib.contextmanager
def span(name: str, *, inputs: Any = None, **attributes: Any) -> Iterator[SpanHandle]:
    """Open an MLflow span if available; otherwise yield a no-op handle.

    Attach `inputs` (and later, via the yielded handle's `set_outputs`) so the
    trace view proves extraction -> scoring -> ranking with receipts (brief
    stretch #1). Token-cost attributes belong wherever a step actually calls a
    served model (e.g. `genie.ask`, or a future Validator) — pass them as
    `attributes` there; `assess_claims` is a pure mapper today and has none.
    """
    mlflow = _get_mlflow()
    if mlflow is None:
        yield SpanHandle(None)
        return
    with mlflow.start_span(name=name) as active:  # pragma: no cover
        handle = SpanHandle(active)
        handle.set_attributes(attributes)
        if inputs is not None:
            handle.set_inputs(inputs)
        yield handle


def traced(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with span(name):
                return fn(*args, **kwargs)

        wrapper.__name__ = getattr(fn, "__name__", "traced")
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator
