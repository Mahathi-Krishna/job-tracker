from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Job:
    """
    Represents one job posting regardless of ATS.
    """

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

    date_posted: Optional[str] = None

    date_found: Optional[str] = None

    description: Optional[str] = None

    def to_row(self):

        return [

            self.date_found,

            self.company,

            self.title,

            self.job_id,

            self.location,

            self.country,

            self.work_mode,

            self.job_type,

            self.experience_level,

            self.ats_platform,

            ", ".join(self.keywords),

            self.score,

            self.url,

            self.date_posted,

            "New"

        ]