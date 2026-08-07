from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class GenericHTMLCollector(BaseCollector):
    """
    Conservative fallback collector for public HTML career pages.

    Only extracts links that appear to represent individual
    job postings.

    No JavaScript execution, authentication, or access-control
    bypassing is performed.
    """

    GENERIC_TITLES = {
        "jobs",
        "careers",
        "career",
        "view jobs",
        "view open roles",
        "open roles",
        "search jobs",
        "search roles",
        "all jobs",
        "find jobs",
        "find a job",
        "apply",
        "apply now",
        "learn more",
        "find out more",
        "students",
        "locations",
        "teams",
        "life at apple",
        "work at apple",
        "benefits",
        "careers at apple",
        "skip to main content",
        "local nav open menu",
        "local nav close menu",
        "click here",
        "register your profile",
        "register your profile on tsmc talent pool",
        "talent pool",
        "join our talent community",
        "join talent community",
    }

    REJECT_PATH_TERMS = (
        "/benefits",
        "/locations",
        "/teams",
        "/students",
        "/life-at-",
        "/work-at-",
        "/culture",
        "/about",
        "/talentcommunity",
        "/talent-community",
        "/login",
        "/signin",
        "/sign-in",
        "/register",
        "/profile",
        "/search",
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

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @classmethod
    def _valid_title(
        cls,
        title: str,
    ) -> bool:

        if not title:
            return False

        title = cls._clean_text(
            title
        )

        if len(title) < 4:
            return False

        if len(title) > 180:
            return False

        if (
            title.casefold()
            in cls.GENERIC_TITLES
        ):
            return False

        lower = title.casefold()

        reject_phrases = (
            "talent pool",
            "talent community",
            "register your profile",
        )

        if any(
            phrase in lower
            for phrase in reject_phrases
        ):
            return False

        return True

    @classmethod
    def _looks_like_job_url(
        cls,
        url: str,
    ) -> bool:

        parsed = urlparse(
            url
        )

        path = parsed.path.lower()

        asset_extensions = (
            ".mp4",
            ".webm",
            ".mov",
            ".avi",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".css",
            ".js",
            ".pdf",
        )

        if path.endswith(
            asset_extensions
        ):
            return False

        query = parse_qs(
            parsed.query
        )

        full = url.lower()

        #
        # Explicit non-job pages.
        #

        for term in (
            cls.REJECT_PATH_TERMS
        ):

            if term in path:
                return False

        #
        # Strong job identifiers.
        #

        query_keys = {
            key.casefold()
            for key in query
        }

        if query_keys & {
            "jobid",
            "job_id",
            "job-id",
            "job",
            "jobreqid",
            "requisitionid",
            "reqid",
        }:
            return True

        #
        # Category/listing pages are not
        # individual job postings.
        #

        category_patterns = (
            "/category/",
            "/categories/",
            "/job-category/",
            "/job-categories/",
        )

        if any(
            pattern in path
            for pattern in category_patterns
        ):
            return False

        #
        # Common individual-job URL
        # structures.
        #

        strong_patterns = (
            "/job/",
            "/jobdetail",
            "/job-detail/",
            "/jobs/",
            "/position/",
            "/positions/",
            "/opening/",
            "/openings/",
            "/requisition/",
        )

        if any(
            pattern in path
            for pattern
            in strong_patterns
        ):

            #
            # Reject the category/search
            # roots themselves.
            #

            stripped = (
                path.rstrip("/")
            )

            if stripped in {
                "/job",
                "/jobs",
                "/career/job",
                "/career/jobs",
                "/careers/job",
                "/careers/jobs",
            }:
                return False

            return True

        #
        # Some career systems encode a
        # numeric posting ID deep in the
        # URL.
        #
        # Example:
        # /job/location/title/44408/96150977248
        #

        if re.search(
            r"/\d{4,}(?:/|$)",
            path,
        ):
            return True

        #
        # A careers/search page alone is
        # NOT an individual posting.
        #

        if (
            "/careers" in full
            and not re.search(
                r"/\d{4,}",
                path,
            )
        ):
            return False

        return False

    @staticmethod
    def _extract_job_id(
        url: str,
    ) -> str:

        parsed = urlparse(
            url
        )

        query = parse_qs(
            parsed.query
        )

        for key in (
            "jobId",
            "jobid",
            "job_id",
            "job-id",
            "jobReqId",
            "requisitionId",
            "reqId",
        ):

            values = query.get(
                key
            )

            if values:
                return str(
                    values[0]
                )

        #
        # Fall back to final substantial
        # numeric URL component.
        #

        numbers = re.findall(
            r"/(\d{4,})(?:/|$)",
            parsed.path,
        )

        if numbers:
            return numbers[-1]

        return ""

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

            href = (
                anchor.get(
                    "href",
                    "",
                )
                .strip()
            )

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

            if (
                absolute_url
                in seen_urls
            ):
                continue

            title = self._clean_text(
                anchor.get_text(
                    " ",
                    strip=True,
                )
            )

            if not (
                self._valid_title(
                    title
                )
            ):
                continue

            seen_urls.add(
                absolute_url
            )

            jobs.append(
                Job(
                    company=company,
                    title=title,
                    url=absolute_url,
                    job_id=(
                        self._extract_job_id(
                            absolute_url
                        )
                    ),
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

        page_html = response.text[
            :self.max_html_chars
        ]

        soup = BeautifulSoup(
            page_html,
            "lxml",
        )

        for element in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "noscript",
                "form",
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