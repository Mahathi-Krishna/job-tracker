from __future__ import annotations

from models.job import Job


class JobValidator:

    INVALID_TITLES = {
        "jobs",
        "careers",
        "career",
        "search jobs",
        "view jobs",
        "open roles",
        "view open roles",
        "apply",
        "apply now",
        "learn more",
        "students",
        "locations",
        "teams",
        "benefits",
    }

    @classmethod
    def is_valid(
        cls,
        job: Job,
    ) -> bool:

        title = (
            job.title
            .strip()
            .casefold()
        )

        if not title:
            return False

        if (
            title
            in cls.INVALID_TITLES
        ):
            return False

        if not job.url.strip():
            return False

        return True