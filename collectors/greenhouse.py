from __future__ import annotations

import html
import re
from urllib.parse import urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from collectors.base import BaseCollector
from models.job import Job


class GreenhouseCollector(BaseCollector):
    """
    Collector for public Greenhouse job boards.

    Uses Greenhouse's public job-board API and does not require
    authentication or browser automation.
    """

    API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; PersonalJobMonitor/1.0)"
                )
            }
        )

    @staticmethod
    def _extract_board_token(career_url: str) -> str:
        """
        Examples:

        https://boards.greenhouse.io/company
        https://job-boards.greenhouse.io/company

        -> company
        """

        parsed = urlparse(career_url)

        parts = [
            part
            for part in parsed.path.split("/")
            if part
        ]

        if not parts:
            raise ValueError(
                f"Cannot determine Greenhouse board from URL: "
                f"{career_url}"
            )

        return parts[0]

    @staticmethod
    def _clean_html(value: str | None) -> str:
        if not value:
            return ""

        value = html.unescape(value)

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=5,
        ),
        reraise=True,
    )
    def _request_jobs(self, board: str) -> dict:

        url = self.API_URL.format(board=board)

        response = self.session.get(
            url,
            params={"content": "true"},
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        board = self._extract_board_token(career_url)

        payload = self._request_jobs(board)

        jobs = []

        for item in payload.get("jobs", []):

            location_data = item.get("location") or {}

            location = (
                location_data.get("name")
                or "Unknown"
            )

            job_id = str(
                item.get("id") or ""
            )

            title = (
                item.get("title")
                or "Unknown"
            ).strip()

            url = (
                item.get("absolute_url")
                or ""
            ).strip()

            description = self._clean_html(
                item.get("content")
            )

            date_posted = (
                item.get("updated_at")
                or None
            )

            jobs.append(
                Job(
                    company=company,
                    title=title,
                    url=url,
                    job_id=job_id,
                    location=location,
                    country="",
                    work_mode="Unknown",
                    job_type="Unknown",
                    experience_level="Unknown",
                    ats_platform="Greenhouse",
                    keywords=[],
                    score=0,
                    date_posted=date_posted,
                    description=description,
                )
            )

        return jobs