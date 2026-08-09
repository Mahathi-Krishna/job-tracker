from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class ArmCollector(BaseCollector):

    SEARCH_URL = (
        "https://careers.arm.com/"
        "en/search-jobs"
    )

    def __init__(
        self,
        timeout: int = 20,
        max_pages: int = 50,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=2,
        )

        self.max_pages = max_pages

    @staticmethod
    def _clean(
        value: str | None,
    ) -> str:

        if not value:
            return ""

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @staticmethod
    def _extract_job_id(
        url: str,
    ) -> str:

        #
        # Arm URLs commonly contain numeric
        # identifiers near the end.
        #

        numbers = re.findall(
            r"/(\d{4,})(?:/|$)",
            url,
        )

        if numbers:
            return numbers[-1]

        return ""

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        jobs = []

        seen_urls = set()

        for page in range(
            1,
            self.max_pages + 1,
        ):

            response = self.http.get(
                self.SEARCH_URL,
                params={
                    "page": page,
                },
                allow_redirects=True,
            )

            soup = BeautifulSoup(
                response.text,
                "lxml",
            )

            page_count = 0

            for anchor in soup.find_all(
                "a",
                href=True,
            ):

                href = (
                    anchor.get(
                        "href",
                        "",
                    )
                    .strip()
                )

                #
                # Arm individual postings
                # use /job/... URLs.
                #

                if "/job/" not in href:
                    continue

                url = urljoin(
                    response.url,
                    href,
                )

                if url in seen_urls:
                    continue

                title = self._clean(
                    anchor.get_text(
                        " ",
                        strip=True,
                    )
                )

                if not title:
                    continue

                if title.casefold() in {
                    "view job",
                    "apply",
                    "apply now",
                    "save job",
                }:
                    continue

                parent = (
                    anchor.find_parent(
                        "li"
                    )
                )

                if parent:

                    text = self._clean(
                        parent.get_text(
                            " ",
                            strip=True,
                        )
                    )

                else:

                    text = title

                #
                # Try to derive location
                # from surrounding text.
                #

                location = text

                if title in location:

                    location = (
                        location.replace(
                            title,
                            "",
                            1,
                        )
                    )

                #
                # Remove common page/card
                # labels.
                #

                location = re.sub(
                    r"\bSave Job\b",
                    "",
                    location,
                    flags=re.IGNORECASE,
                )

                location = self._clean(
                    location
                )

                job_id = (
                    self._extract_job_id(
                        url
                    )
                )

                job = Job(
                    company=company,
                    title=title,
                    url=url,
                    job_id=job_id,
                    location=(
                        location
                        or "Unknown"
                    ),
                    country="",
                    work_mode="Unknown",
                    job_type="Unknown",
                    experience_level=(
                        "Unknown"
                    ),
                    ats_platform=(
                        "Arm Careers"
                    ),
                    keywords=[],
                    score=0,
                    date_posted=None,
                    description=None,
                )

                jobs.append(
                    job
                )

                seen_urls.add(
                    url
                )

                page_count += 1

            if page_count == 0:
                break

        return jobs

    def enrich(
        self,
        job: Job,
    ) -> Job:

        response = self.http.get(
            job.url,
            allow_redirects=True,
        )

        soup = BeautifulSoup(
            response.text,
            "lxml",
        )

        for element in soup(
            [
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "form",
                "noscript",
            ]
        ):

            element.decompose()

        job.description = (
            self._clean(
                soup.get_text(
                    " ",
                    strip=True,
                )
            )
        )

        return job