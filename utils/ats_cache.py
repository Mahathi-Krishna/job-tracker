from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

CACHE_PATH = (
    PROJECT_ROOT
    / "data"
    / "ats_cache.json"
)


class ATSCache:
    """
    Small persistent cache for ATS discovery.

    This avoids repeatedly inspecting company
    career pages on every monitor run.
    """

    def __init__(
        self,
        retention_days: int = 7,
    ):

        self.retention_days = (
            retention_days
        )

        CACHE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.data = self._load()

    def _load(
        self,
    ) -> dict:

        if not CACHE_PATH.exists():
            return {}

        try:

            with CACHE_PATH.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )

            if isinstance(
                data,
                dict,
            ):
                return data

        except (
            json.JSONDecodeError,
            OSError,
        ):
            pass

        return {}

    def _save(
        self,
    ) -> None:

        temporary = (
            CACHE_PATH.with_suffix(
                ".tmp"
            )
        )

        with temporary.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.data,
                file,
                indent=2,
                sort_keys=True,
            )

        temporary.replace(
            CACHE_PATH
        )

    @staticmethod
    def _key(
        company: str,
        configured_url: str,
    ) -> str:

        return (
            f"{company.strip()}|"
            f"{configured_url.strip()}"
        )

    def get(
        self,
        company: str,
        configured_url: str,
    ) -> dict | None:

        key = self._key(
            company,
            configured_url,
        )

        entry = self.data.get(
            key
        )

        if not entry:
            return None

        updated_at = entry.get(
            "updated_at"
        )

        if not updated_at:
            return None

        try:

            timestamp = (
                datetime.fromisoformat(
                    updated_at
                )
            )

        except ValueError:
            return None

        if timestamp.tzinfo is None:

            timestamp = (
                timestamp.replace(
                    tzinfo=timezone.utc
                )
            )

        cutoff = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=self.retention_days
            )
        )

        if timestamp < cutoff:
            return None

        return entry

    def set(
        self,
        company: str,
        configured_url: str,
        ats: str,
        detected_url: str,
        detected_by: str,
    ) -> None:

        key = self._key(
            company,
            configured_url,
        )

        self.data[key] = {
            "ats": ats,
            "url": detected_url,
            "detected_by": (
                detected_by
            ),
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat(
                    timespec="seconds"
                )
            ),
        }

        self._save()

    def clear(
        self,
    ) -> None:

        self.data = {}

        self._save()