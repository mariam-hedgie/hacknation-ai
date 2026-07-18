"""Lightweight, file-backed user profiles for the Aven demo.

This is a safe local fallback, mirroring the rest of the app: no real auth, no
challenge data. A logged-in profile persists to a local JSON file keyed by email
so history, hospital ratings, and the "never refer me here" blocklist survive
across visits. Guests get the same in-memory profile shape without persistence.

A production build would replace this store with Lakebase or an approved
Databricks write path behind the same function signatures.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

# Sits beside the app; gitignored so demo profiles never get committed.
_STORE = Path(__file__).resolve().parent.parent / ".aven_profiles.json"


def empty_profile(name: str = "", email: str = "") -> dict[str, Any]:
    """Return a fresh profile with every expected key present."""
    return {
        "name": name,
        "email": email,
        "history": [],   # submitted requests: {ts, care_task, capability, location}
        "saved": [],     # saved referrals: {facility, label, care_task}
        "ratings": {},   # facility -> {"rating": 1-5, "note": str}
        "blocklist": [], # facility names the user never wants referred again
    }


def _normalize(data: dict[str, Any], email: str) -> dict[str, Any]:
    base = empty_profile(email=email)
    base.update(data or {})
    # Defend against older/partial records missing newer keys.
    for key, default in empty_profile().items():
        base.setdefault(key, default)
    return base


def _load_store() -> dict[str, Any]:
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_store(store: dict[str, Any]) -> None:
    try:
        _STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        # Read-only filesystem or similar: fail safe, keep session-only behavior.
        pass


def load_profile(email: str) -> dict[str, Any]:
    """Load a persisted profile by email, or a fresh one if none exists."""
    key = (email or "").strip().lower()
    if not key:
        return empty_profile(email=email)
    return _normalize(_load_store().get(key, {}), email)


def save_profile(profile: dict[str, Any]) -> None:
    """Persist a profile keyed by its email. No-op for profiles without an email
    (i.e. guests), so guest activity never touches disk."""
    key = (profile.get("email") or "").strip().lower()
    if not key:
        return
    store = _load_store()
    store[key] = profile
    _save_store(store)


def add_history(profile: dict[str, Any], request: dict[str, Any]) -> None:
    profile["history"].insert(0, {
        "ts": time.time(),
        "care_task": request.get("care_task", ""),
        "capability": request.get("capability", ""),
        "location": request.get("location", ""),
    })
    del profile["history"][40:]  # keep the log bounded


def add_saved(profile: dict[str, Any], option: dict[str, Any], care_task: str) -> None:
    facility = option.get("facility", "")
    if any(item["facility"] == facility for item in profile["saved"]):
        return
    profile["saved"].insert(0, {
        "facility": facility,
        "label": option.get("label", ""),
        "care_task": care_task,
    })


def set_rating(profile: dict[str, Any], facility: str, rating: int, note: str = "") -> None:
    profile["ratings"][facility] = {"rating": int(rating), "note": note}


def get_rating(profile: dict[str, Any], facility: str) -> int | None:
    entry = profile["ratings"].get(facility)
    return entry["rating"] if entry else None


def block_facility(profile: dict[str, Any], facility: str) -> None:
    if facility and facility not in profile["blocklist"]:
        profile["blocklist"].append(facility)


def unblock_facility(profile: dict[str, Any], facility: str) -> None:
    if facility in profile["blocklist"]:
        profile["blocklist"].remove(facility)


def is_blocked(profile: dict[str, Any], facility: str) -> bool:
    return facility in profile["blocklist"]
