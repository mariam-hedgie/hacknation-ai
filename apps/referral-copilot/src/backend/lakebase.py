"""Lakebase seam — persist notes, overrides, shortlists, ratings, blocklist.

The brief requires user actions to survive beyond a single session. This wraps
persistence behind one interface. Until Lakebase is wired, it delegates to the
local JSON store in `src/profiles.py` (logged-in) / session state (guests), so
behavior is identical and swapping the backend is a one-file change.
"""

from __future__ import annotations

from typing import Any

from .. import profiles as local_profiles
from .config import BackendConfig


class LakebasePersistence:
    def __init__(self, config: BackendConfig) -> None:
        self._config = config

    def available(self) -> bool:
        return self._config.has_lakebase

    def load_profile(self, email: str) -> dict[str, Any]:
        """Load a user's persisted profile (history, ratings, blocklist, saved).

        TODO(lakebase):
          - Read the profile row(s) for `email` from the Lakebase Postgres
            instance (self._config.lakebase_url) and hydrate the same dict shape
            profiles.empty_profile() returns.
          - On any connection error, fall through to the local store below so a
            live-demo outage never loses the session.
        """
        if self.available():
            # profile = _read_lakebase(email); if profile: return profile
            pass
        return local_profiles.load_profile(email)

    def save_profile(self, profile: dict[str, Any]) -> None:
        """Persist a user's profile.

        TODO(lakebase): UPSERT into the Lakebase profiles table keyed by email.
        Keep the local write as a mirror/fallback for offline demos.
        """
        if self.available():
            # _write_lakebase(profile)
            pass
        local_profiles.save_profile(profile)
