from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class WorkdayCollector(BaseCollector):
    """
    Collector for public Workday external career sites.

    Workday URLs normally have this structure:

    https://<tenant>.<datacenter>.myworkdayjobs.com/<site>
    """

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

        parsed = urlparse(career_url)

        hostname = parsed.netloc.lower()

        if "myworkdayjobs.com" not in hostname:
            raise ValueError(
                "Not a Workday career URL: "
                f"{career_url}"
            )

        parts = [
            part
            for part in parsed.path.split("/")
            if part
        ]

        if not parts:
            raise ValueError(
                "Workday URL is missing the "
                f"external career site: {career_url}"
            )

        site = parts[0]

        base_url = (
            f"{parsed.scheme}://{parsed.netloc}"
        )

        return base_url, site, hostname

    def _search_endpoint(
        self,
        career_url: str,
    ) -> tuple[str, str]:

        base_url, site, _ = (
            self._parse_workday_url(
                career_url
            )
        )

        endpoint = (
            f"{base_url}/wday/cxs/"
            f"{self._tenant_from_host(base_url)}/"
            f"{site}/jobs"
        )

        return endpoint, site

    @staticmethod
    def _tenant_from_host(
        base_url: str,
    ) -> str:

        hostname = urlparse(
            base_url
        ).netloc

        # Example:
        #
        # nvidia.wd5.myworkdayjobs.com
        #
        # -> nvidia

        tenant = hostname.split(".")[0]

        if not tenant:
            raise ValueError(
                f"Cannot determine Workday tenant: "
                f"{base_url}"
            )

        return tenant

    def _fetch_page(
        self,
        endpoint: str,
        offset: int,
    ) -> dict:

        payload = {
            "appliedFacets": {},
            "limit": self.PAGE_SIZE,
            "offset": offset,
            "searchText": "",
        }

        response = self.http.post(
            endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        return response.json()

    @staticmethod
    def _extract_postings(
        payload: dict,
    ) -> list[dict]:

        postings = payload.get(
            "jobPostings",
            []
        )

        if not isinstance(postings, list):
            return []

        return postings

    def _fetch_detail(
        self,
        base_url: str,
        site: str,
        tenant: str,
        external_path: str,
    ) -> dict:

        path = external_path

        if not path.startswith("/"):
            path = "/" + path

        endpoint = (
            f"{base_url}/wday/cxs/"
            f"{tenant}/{site}"
            f"{path}"
        )

        response = self.http.get(
            endpoint,
            headers={
                "Accept": "application/json",
            },
        )

        return response.json()

    @staticmethod
    def _strip_html(
        text: str | None,
    ) -> str:

        if not text:
            return ""

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        base_url, site, _ = (
            self._parse_workday_url(
                career_url
            )
        )

        tenant = self._tenant_from_host(
            base_url
        )

        endpoint = (
            f"{base_url}/wday/cxs/"
            f"{tenant}/{site}/jobs"
        )

        jobs = []

        offset = 0

        page_number = 0

        while page_number < self.max_pages:

            payload = self._fetch_page(
                endpoint,
                offset,
            )

            postings = self._extract_postings(
                payload
            )

            if not postings:
                break

            for posting in postings:

                title = (
                    posting.get("title")
                    or "Unknown"
                ).strip()

                external_path = (
                    posting.get("externalPath")
                    or ""
                )

                location = (
                    posting.get("locationsText")
                    or "Unknown"
                )

                posted_on = (
                    posting.get("postedOn")
                    or None
                )

                bullet_fields = (
                    posting.get("bulletFields")
                    or []
                )

                job_id = ""

                if bullet_fields:
                    job_id = str(
                        bullet_fields[0]
                    )

                posting_url = urljoin(
                    f"{base_url}/{site}/",
                    external_path,
                )

                description = ""

                #
                # Do NOT fetch every job detail here.
                #
                # Listing-level information is enough
                # for the initial filtering pass.
                #

                jobs.append(
                    Job(
                        company=company,
                        title=title,
                        url=posting_url,
                        job_id=job_id,
                        location=location,
                        country="",
                        work_mode="Unknown",
                        job_type="Unknown",
                        experience_level="Unknown",
                        ats_platform="Workday",
                        keywords=[],
                        score=0,
                        date_posted=posted_on,
                        description=description,
                    )
                )

            total = payload.get(
                "total",
                0,
            )

            offset += len(postings)
            page_number += 1

            if offset >= total:
                break

        return jobs