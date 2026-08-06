from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import Any


@dataclass(slots=True)
class Job:

    company: str
    title: str
    url: str
    job_id: str
    location: str
    country: str
    work_mode: str
    job_type: str
    experience_level: str
    ats_platform: str
    keywords: list[str]
    score: int

    date_posted: str | None = None
    date_found: str | None = None
    description: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
    )

    def to_row(
        self,
    ) -> list:

        return [
            self.date_found or "",
            self.company,
            self.title,
            self.job_id,
            self.location,
            self.country,
            self.work_mode,
            self.job_type,
            self.experience_level,
            self.ats_platform,
            ", ".join(
                self.keywords
            ),
            self.score,
            self.url,
            self.date_posted or "",
            "New",
        ]