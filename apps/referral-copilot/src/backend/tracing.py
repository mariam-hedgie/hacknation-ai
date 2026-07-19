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


@contextlib.contextmanager
def span(name: str, **attributes: Any) -> Iterator[None]:
    """Open an MLflow span if available; otherwise do nothing.

    TODO(mlflow): attach inputs/outputs and token-cost attributes so the trace
    view proves extraction -> scoring -> ranking with receipts (brief stretch #1).
    """
    mlflow = _get_mlflow()
    if mlflow is None:
        yield
        return
    with mlflow.start_span(name=name) as active:  # pragma: no cover
        try:
            if attributes:
                active.set_attributes(attributes)
        except Exception:
            pass
        yield


def traced(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with span(name):
                return fn(*args, **kwargs)

        wrapper.__name__ = getattr(fn, "__name__", "traced")
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator
