from __future__ import annotations

import html
import re
from urllib.parse import urlparse

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class AshbyCollector(BaseCollector):

    API_URL = (
        "https://api.ashbyhq.com/"
        "posting-api/job-board/{board}"
    )

    def __init__(
        self,
        timeout: int = 20,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=3,
        )

    @staticmethod
    def _extract_board(
        career_url: str,
    ) -> str:

        parsed = urlparse(
            career_url
        )

        parts = [
            part
            for part
            in parsed.path.split("/")
            if part
        ]

        if not parts:

            raise ValueError(
                "Cannot determine Ashby "
                f"board from {career_url}"
            )

        return parts[0]

    @staticmethod
    def _clean_html(
        value: str | None,
    ) -> str:

        if not value:
            return ""

        value = html.unescape(
            value
        )

        value = re.sub(
            r"<[^>]+>",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        board = self._extract_board(
            career_url
        )

        response = self.http.get(
            self.API_URL.format(
                board=board
            ),
            params={
                "includeCompensation":
                    "false"
            },
            headers={
                "Accept":
                    "application/json",
            },
        )

        payload = response.json()

        jobs = []

        for item in payload.get(
            "jobs",
            [],
        ):

            if (
                item.get("isListed")
                is False
            ):
                continue

            location = (
                item.get("location")
                or "Unknown"
            )

            description = (
                item.get(
                    "descriptionPlain"
                )
                or item.get(
                    "description"
                )
                or ""
            )

            description = (
                self._clean_html(
                    description
                )
            )

            job_url = (
                item.get("jobUrl")
                or item.get("applyUrl")
                or ""
            )

            job_id = str(
                item.get("id")
                or ""
            )

            jobs.append(
                Job(
                    company=company,
                    title=(
                        item.get("title")
                        or "Unknown"
                    ).strip(),
                    url=job_url,
                    job_id=job_id,
                    location=location,
                    country="",
                    work_mode=(
                        "Remote"
                        if item.get(
                            "isRemote"
                        )
                        else "Unknown"
                    ),
                    job_type=(
                        item.get(
                            "employmentType"
                        )
                        or "Unknown"
                    ),
                    experience_level=(
                        "Unknown"
                    ),
                    ats_platform="Ashby",
                    keywords=[],
                    score=0,
                    date_posted=(
                        item.get(
                            "publishedAt"
                        )
                        or None
                    ),
                    description=(
                        description
                    ),
                )
            )

        return jobs