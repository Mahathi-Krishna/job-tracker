from __future__ import annotations

import html
import re
from urllib.parse import urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from collectors.base import BaseCollector
from models.job import Job


class LeverCollector(BaseCollector):
    """
    Collector for public Lever job boards.
    """

    API_URL = "https://api.lever.co/v0/postings/{site}"

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
    def _extract_site(career_url: str) -> str:

        parsed = urlparse(career_url)

        parts = [
            part
            for part in parsed.path.split("/")
            if part
        ]

        if not parts:
            raise ValueError(
                f"Cannot determine Lever site from URL: "
                f"{career_url}"
            )

        return parts[0]

    @staticmethod
    def _clean_text(value: str | None) -> str:

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
    def _request_jobs(self, site: str) -> list:

        response = self.session.get(
            self.API_URL.format(site=site),
            params={"mode": "json"},
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        site = self._extract_site(career_url)

        payload = self._request_jobs(site)

        jobs = []

        for item in payload:

            categories = (
                item.get("categories")
                or {}
            )

            location = (
                categories.get("location")
                or "Unknown"
            )

            commitment = (
                categories.get("commitment")
                or "Unknown"
            )

            description_parts = [
                item.get("descriptionPlain") or "",
                item.get("additionalPlain") or "",
            ]

            description = self._clean_text(
                " ".join(description_parts)
            )

            jobs.append(
                Job(
                    company=company,
                    title=(
                        item.get("text")
                        or "Unknown"
                    ).strip(),
                    url=(
                        item.get("hostedUrl")
                        or item.get("applyUrl")
                        or ""
                    ).strip(),
                    job_id=str(
                        item.get("id")
                        or ""
                    ),
                    location=location,
                    country="",
                    work_mode="Unknown",
                    job_type=commitment,
                    experience_level="Unknown",
                    ats_platform="Lever",
                    keywords=[],
                    score=0,
                    date_posted=None,
                    description=description,
                )
            )

        return jobs