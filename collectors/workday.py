from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlparse

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class WorkdayCollector(BaseCollector):

    PAGE_SIZE = 20

    def __init__(
        self,
        timeout: int = 20,
        max_pages: int = 200,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=3,
        )

        self.max_pages = max_pages

    @staticmethod
    def _parse_workday_url(
        career_url: str,
    ) -> tuple[str, str, str]:

        parsed = urlparse(
            career_url
        )

        hostname = (
            parsed.netloc.lower()
        )

        if (
            "myworkdayjobs.com"
            not in hostname
        ):
            raise ValueError(
                "Not a Workday URL: "
                f"{career_url}"
            )

        path_parts = [
            part
            for part
            in parsed.path.split("/")
            if part
        ]

        if not path_parts:

            raise ValueError(
                "Missing Workday career site: "
                f"{career_url}"
            )

        #
        # Workday URLs may contain a locale:
        #
        # /en-US/sifivecareers
        # /en-US/External
        #
        # The career site is the component
        # AFTER the locale.
        #

        locale_pattern = re.compile(
            r"^[a-z]{2}-[A-Z]{2}$"
        )

        if (
            len(path_parts) >= 2
            and locale_pattern.match(
                path_parts[0]
            )
        ):
            site = path_parts[1]

        else:
            site = path_parts[0]

        base_url = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
        )

        tenant = (
            parsed.netloc.split(".")[0]
        )

        return (
            base_url,
            tenant,
            site,
        )
    
    def _jobs_endpoint(
        self,
        base_url: str,
        tenant: str,
        site: str,
    ) -> str:

        return (
            f"{base_url}/wday/cxs/"
            f"{tenant}/{site}/jobs"
        )

    def _fetch_page(
        self,
        endpoint: str,
        offset: int,
    ) -> dict:

        response = self.http.post(
            endpoint,
            json={
                "appliedFacets": {},
                "limit": self.PAGE_SIZE,
                "offset": offset,
                "searchText": "",
            },
            headers={
                "Accept":
                    "application/json",
                "Content-Type":
                    "application/json",
            },
        )

        return response.json()

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        (
            base_url,
            tenant,
            site,
        ) = self._parse_workday_url(
            career_url
        )

        endpoint = self._jobs_endpoint(
            base_url,
            tenant,
            site,
        )

        jobs = []

        offset = 0

        for _ in range(
            self.max_pages
        ):

            payload = self._fetch_page(
                endpoint,
                offset,
            )

            postings = payload.get(
                "jobPostings",
                [],
            )

            if not postings:
                break

            for posting in postings:

                external_path = (
                    posting.get(
                        "externalPath"
                    )
                    or ""
                )

                public_url = urljoin(
                    f"{base_url}/{site}/",
                    external_path,
                )

                bullet_fields = (
                    posting.get(
                        "bulletFields"
                    )
                    or []
                )

                job_id = ""

                if bullet_fields:
                    job_id = str(
                        bullet_fields[0]
                    )

                job = Job(
                    company=company,
                    title=(
                        posting.get(
                            "title"
                        )
                        or "Unknown"
                    ).strip(),
                    url=public_url,
                    job_id=job_id,
                    location=(
                        posting.get(
                            "locationsText"
                        )
                        or "Unknown"
                    ),
                    country="",
                    work_mode="Unknown",
                    job_type="Unknown",
                    experience_level=(
                        "Unknown"
                    ),
                    ats_platform=(
                        "Workday"
                    ),
                    keywords=[],
                    score=0,
                    date_posted=(
                        posting.get(
                            "postedOn"
                        )
                        or None
                    ),
                    description=None,
                )

                # Store internal information
                # required by enrich() without
                # adding database fields.

                job.metadata.update(
                    {
                        "workday_base_url":
                            base_url,
                        "workday_tenant":
                            tenant,
                        "workday_site":
                            site,
                        "workday_path":
                            external_path,
                    }
                )

                jobs.append(job)

            total = int(
                payload.get(
                    "total",
                    0,
                )
                or 0
            )

            offset += len(
                postings
            )

            if (
                total
                and offset >= total
            ):
                break

        return jobs

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

    def enrich(
        self,
        job: Job,
    ) -> Job:

        base_url = job.metadata.get(
            "workday_base_url"
        )

        tenant = job.metadata.get(
            "workday_tenant"
        )

        site = job.metadata.get(
            "workday_site"
        )

        external_path = job.metadata.get(
            "workday_path"
        )

        if not all(
            [
                base_url,
                tenant,
                site,
                external_path,
            ]
        ):
            return job

        if not external_path.startswith(
            "/"
        ):
            external_path = (
                "/"
                + external_path
            )

        endpoint = (
            f"{base_url}/wday/cxs/"
            f"{tenant}/{site}"
            f"{external_path}"
        )

        response = self.http.get(
            endpoint,
            headers={
                "Accept":
                    "application/json",
            },
        )

        payload = response.json()

        job_info = payload.get(
            "jobPostingInfo",
            {},
        )

        job.description = (
            self._clean_html(
                job_info.get(
                    "jobDescription"
                )
            )
        )

        if not job.job_id:

            job.job_id = str(
                job_info.get(
                    "jobReqId"
                )
                or ""
            )

        return job