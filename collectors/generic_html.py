from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class GenericHTMLCollector(BaseCollector):
    """
    Conservative collector for public HTML career pages.

    It does NOT execute JavaScript and does NOT attempt
    to bypass authentication or access controls.

    It only extracts links that are already present in
    the returned public HTML.
    """

    JOB_TERMS = (
        "/job/",
        "/jobs/",
        "/career/",
        "/careers/",
        "jobid=",
        "job_id=",
        "job-id=",
        "requisition",
    )

    IGNORE_TERMS = (
        "/login",
        "/signin",
        "/sign-in",
        "/register",
        "/profile",
        "/talent-community",
        "/connect",
    )

    def __init__(
        self,
        timeout: int = 20,
        max_html_chars: int = 2_000_000,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=2,
        )

        self.max_html_chars = (
            max_html_chars
        )

    @classmethod
    def _looks_like_job_url(
        cls,
        url: str,
    ) -> bool:

        lower = url.lower()

        if any(
            term in lower
            for term in cls.IGNORE_TERMS
        ):
            return False

        return any(
            term in lower
            for term in cls.JOB_TERMS
        )

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        response = self.http.get(
            career_url,
            allow_redirects=True,
            headers={
                "Accept":
                    "text/html,"
                    "application/xhtml+xml",
            },
        )

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            ).lower()
        )

        if "html" not in content_type:

            return []

        page_html = response.text[
            :self.max_html_chars
        ]

        soup = BeautifulSoup(
            page_html,
            "lxml",
        )

        jobs = []

        seen_urls = set()

        for anchor in soup.find_all(
            "a",
            href=True,
        ):

            href = anchor.get(
                "href",
                "",
            ).strip()

            if not href:
                continue

            absolute_url = urljoin(
                response.url,
                href,
            )

            if not (
                self._looks_like_job_url(
                    absolute_url
                )
            ):
                continue

            if absolute_url in seen_urls:
                continue

            title = self._clean_text(
                anchor.get_text(
                    " ",
                    strip=True,
                )
            )

            #
            # Empty/generic anchors aren't
            # useful job postings.
            #

            if (
                not title
                or len(title) < 3
            ):
                continue

            lower_title = (
                title.casefold()
            )

            if lower_title in {
                "jobs",
                "careers",
                "view jobs",
                "search jobs",
                "all jobs",
                "apply",
                "apply now",
                "learn more",
            }:
                continue

            seen_urls.add(
                absolute_url
            )

            jobs.append(
                Job(
                    company=company,
                    title=title,
                    url=absolute_url,
                    job_id="",
                    location="Unknown",
                    country="",
                    work_mode="Unknown",
                    job_type="Unknown",
                    experience_level=(
                        "Unknown"
                    ),
                    ats_platform=(
                        "Public HTML"
                    ),
                    keywords=[],
                    score=0,
                    date_posted=None,
                    description=None,
                )
            )

        return jobs

    def enrich(
        self,
        job: Job,
    ) -> Job:

        response = self.http.get(
            job.url,
            allow_redirects=True,
            headers={
                "Accept":
                    "text/html,"
                    "application/xhtml+xml",
            },
        )

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            ).lower()
        )

        if "html" not in content_type:
            return job

        soup = BeautifulSoup(
            response.text[
                :self.max_html_chars
            ],
            "lxml",
        )

        #
        # Remove page chrome/noise.
        #

        for element in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "noscript",
            ]
        ):
            element.decompose()

        text = soup.get_text(
            " ",
            strip=True,
        )

        job.description = (
            self._clean_text(
                text
            )
        )

        return job