from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class SynopsysCollector(BaseCollector):
    """
    Collector for the public Synopsys careers site.

    Uses normal public HTML pages only.
    No browser automation or authentication.
    """

    SEARCH_URL = (
        "https://careers.synopsys.com/"
        "search-jobs"
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
        text: str,
        url: str,
    ) -> str:

        match = re.search(
            r"Job ID:\s*(\d+)",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        #
        # Synopsys job-detail URLs normally
        # contain the numeric requisition ID.
        #

        numbers = re.findall(
            r"/(\d{4,})(?:/|$)",
            url,
        )

        if numbers:
            return numbers[-1]

        return ""

    @staticmethod
    def _extract_date(
        text: str,
    ) -> str | None:

        match = re.search(
            r"Posted:\s*"
            r"(\d{1,2}/\d{1,2}/\d{4})",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return None

    @staticmethod
    def _extract_location(
        text: str,
        title: str,
    ) -> str:

        cleaned = text

        if title:
            cleaned = cleaned.replace(
                title,
                "",
                1,
            )

        cleaned = re.sub(
            r"Category:.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"Posted:.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"Job ID:.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^\s*Save\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        return re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

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
                    "acm": "ALL",
                    "alrpm": "ALL",
                    "page": page,
                },
                allow_redirects=True,
            )

            soup = BeautifulSoup(
                response.text,
                "lxml",
            )

            page_jobs = 0

            #
            # Individual job links on the
            # public Synopsys results page.
            #

            for anchor in soup.find_all(
                "a",
                href=True,
            ):

                href = anchor.get(
                    "href",
                    "",
                )

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
                    "save",
                }:
                    continue

                #
                # Job metadata is usually in
                # the surrounding list item.
                #

                parent = anchor.find_parent(
                    "li"
                )

                if parent is None:

                    parent = (
                        anchor.parent
                    )

                surrounding_text = (
                    self._clean(
                        parent.get_text(
                            " ",
                            strip=True,
                        )
                    )
                    if parent
                    else title
                )

                job_id = (
                    self._extract_job_id(
                        surrounding_text,
                        url,
                    )
                )

                location = (
                    self._extract_location(
                        surrounding_text,
                        title,
                    )
                )

                date_posted = (
                    self._extract_date(
                        surrounding_text
                    )
                )

                jobs.append(
                    Job(
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
                            "Synopsys Careers"
                        ),
                        keywords=[],
                        score=0,
                        date_posted=(
                            date_posted
                        ),
                        description=None,
                    )
                )

                seen_urls.add(
                    url
                )

                page_jobs += 1

            #
            # No postings means we've
            # reached the end.
            #

            if page_jobs == 0:
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