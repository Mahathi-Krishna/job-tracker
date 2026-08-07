from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from models.job import Job


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
)


class DryRunReporter:

    def __init__(
        self,
        limit: int = 200,
    ):

        self.limit = max(
            int(limit),
            1,
        )

        self.jobs: list[Job] = []

    def add(
        self,
        job: Job,
    ) -> None:

        if (
            len(self.jobs)
            >= self.limit
        ):
            return

        self.jobs.append(
            job
        )

    @staticmethod
    def _clean(
        value: str | None,
    ) -> str:

        if not value:
            return ""

        return (
            str(value)
            .replace(
                "\r",
                " ",
            )
            .replace(
                "\n",
                " ",
            )
            .strip()
        )

    def write(
        self,
    ) -> Path:

        REPORT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            REPORT_DIR
            / "dry_run_report.txt"
        )

        now = datetime.now(
            timezone.utc
        )

        lines = [
            "JOB MONITOR DRY RUN",
            "=" * 120,
            (
                "Generated UTC: "
                + now.isoformat(
                    timespec="seconds"
                )
            ),
            (
                "Jobs shown: "
                f"{len(self.jobs)}"
            ),
            "=" * 120,
            "",
        ]

        for number, job in enumerate(
            self.jobs,
            start=1,
        ):

            lines.extend(
                [
                    (
                        f"[{number}] "
                        f"{self._clean(job.company)}"
                    ),
                    (
                        "Title: "
                        f"{self._clean(job.title)}"
                    ),
                    (
                        "Job ID: "
                        f"{self._clean(job.job_id)}"
                    ),
                    (
                        "Location: "
                        f"{self._clean(job.location)}"
                    ),
                    (
                        "Country: "
                        f"{self._clean(job.country)}"
                    ),
                    (
                        "Work Mode: "
                        f"{self._clean(job.work_mode)}"
                    ),
                    (
                        "Job Type: "
                        f"{self._clean(job.job_type)}"
                    ),
                    (
                        "Experience: "
                        f"{self._clean(job.experience_level)}"
                    ),
                    (
                        "ATS: "
                        f"{self._clean(job.ats_platform)}"
                    ),
                    (
                        "Score: "
                        f"{job.score}"
                    ),
                    (
                        "Keywords: "
                        + ", ".join(
                            job.keywords
                        )
                    ),
                    (
                        "Date Posted: "
                        f"{self._clean(job.date_posted)}"
                    ),
                    (
                        "URL: "
                        f"{self._clean(job.url)}"
                    ),
                    "-" * 120,
                ]
            )

        path.write_text(
            "\n".join(
                lines
            ),
            encoding="utf-8",
        )

        return path