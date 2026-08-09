from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlparse

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class WorkdayCollector(BaseCollector):

    #
    # Workday tenants commonly enforce a
    # relatively small maximum page size.
    # NVIDIA rejects 100 with HTTP 400.
    #
    PAGE_SIZE = 20

    def __init__(
        self,
        timeout: int = 20,
        max_pages: int = 100,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=3,
        )

        self.max_pages = max_pages

        self.title_filter = None

    def set_title_filter(
        self,
        title_filter,
    ) -> None:

        self.title_filter = (
            title_filter
        )

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
            parsed.netloc.split(
                "."
            )[0]
        )

        return (
            base_url,
            tenant,
            site,
        )

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
                "limit":
                    self.PAGE_SIZE,
                "offset":
                    offset,
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

    @staticmethod
    def _extract_job_id(
        posting: dict,
        external_path: str,
    ) -> str:
        """
        Extract a Workday requisition ID.

        Workday's bulletFields are inconsistent
        between tenants. Some contain the requisition
        ID, while others contain values such as
        'Posted 7 Days Ago'.

        Prefer recognizable requisition IDs, then
        fall back to the external posting path.
        """

        bullet_fields = (
            posting.get("bulletFields")
            or []
        )

        for value in bullet_fields:

            value = str(value).strip()

            if not value:
                continue

            #
            # Common Workday IDs:
            #
            # R55703
            # R-101291
            # JR2022759
            # 20658
            #

            if re.fullmatch(
                r"(?:JR|R-?)?\d{4,}",
                value,
                flags=re.IGNORECASE,
            ):
                return value

        #
        # Fall back to URL/path.
        #
        # Examples:
        #
        # ..._JR2022759
        # ..._R55703
        # ..._R-101291-1
        # ..._20658-1
        #

        filename = (
            external_path
            .rstrip("/")
            .split("/")[-1]
        )

        patterns = (
            r"_(JR\d+)(?:-\d+)?$",
            r"_(R-\d+)(?:-\d+)?$",
            r"_(R\d+)(?:-\d+)?$",
            r"_(\d{4,})(?:-\d+)?$",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                filename,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1)

        return ""

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

        endpoint = (
            self._jobs_endpoint(
                base_url,
                tenant,
                site,
            )
        )

        jobs = []

        offset = 0

        for _ in range(
            self.max_pages
        ):

            payload = (
                self._fetch_page(
                    endpoint,
                    offset,
                )
            )

            postings = (
                payload.get(
                    "jobPostings",
                    [],
                )
            )

            if not postings:
                break

            for posting in postings:

                title = (
                    posting.get(
                        "title"
                    )
                    or "Unknown"
                ).strip()

                #
                # High-volume optimization.
                #
                # Reject irrelevant titles
                # before constructing Job
                # objects or sending them
                # downstream.
                #

                if (
                    self.title_filter
                    is not None
                    and not
                    self.title_filter.matches(
                        title
                    )
                ):

                    continue

                external_path = (
                    posting.get(
                        "externalPath"
                    )
                    or ""
                )

                normalized_path = (
                    external_path
                    if external_path.startswith("/")
                    else "/" + external_path
                )

                public_url = (
                    f"{base_url}/"
                    f"{site}"
                    f"{normalized_path}"
                )

                job_id = self._extract_job_id(
                    posting,
                    external_path,
                )

                location = (
                    posting.get(
                        "locationsText"
                    )
                    or "Unknown"
                )

                #
                # Workday sometimes returns:
                #
                #   "2 Locations"
                #   "3 Locations"
                #
                # while externalPath contains a useful
                # primary location:
                #
                # /job/US-CA-Santa-Clara/...
                # /job/India-Bengaluru/...
                #

                if re.fullmatch(
                    r"\d+\s+Locations?",
                    location,
                    flags=re.IGNORECASE,
                ):

                    path_parts = [
                        part
                        for part
                        in external_path.split("/")
                        if part
                    ]

                    if (
                        len(path_parts) >= 2
                        and path_parts[0].lower()
                        == "job"
                    ):

                        location = (
                            path_parts[1]
                            .replace(
                                "-",
                                " ",
                            )
                        )

                job = Job(
                    company=company,
                    title=title,
                    url=public_url,
                    job_id=job_id,
                    location=location,
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

                jobs.append(
                    job
                )

            total = int(
                payload.get(
                    "total",
                    0,
                )
                or 0
            )

            #
            # Important:
            #
            # offset advances according
            # to RAW postings returned,
            # not relevant jobs retained.
            #

            offset += len(
                postings
            )

            if (
                total
                and offset >= total
            ):
                break

        return jobs

    def enrich(
        self,
        job: Job,
    ) -> Job:

        base_url = (
            job.metadata.get(
                "workday_base_url"
            )
        )

        tenant = (
            job.metadata.get(
                "workday_tenant"
            )
        )

        site = (
            job.metadata.get(
                "workday_site"
            )
        )

        external_path = (
            job.metadata.get(
                "workday_path"
            )
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

        if not (
            external_path.startswith(
                "/"
            )
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

        job_info = (
            payload.get(
                "jobPostingInfo",
                {},
            )
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