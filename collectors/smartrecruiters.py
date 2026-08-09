from __future__ import annotations

from urllib.parse import urlparse

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class SmartRecruitersCollector(
    BaseCollector
):

    API_URL = (
        "https://api.smartrecruiters.com/"
        "v1/companies/{company}/postings"
    )

    PAGE_SIZE = 100

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

    @staticmethod
    def _extract_company_identifier(
        career_url: str,
    ) -> str:

        parsed = urlparse(
            career_url
        )

        parts = [
            part
            for part in parsed.path.split("/")
            if part
        ]

        if not parts:

            raise ValueError(
                "SmartRecruiters URL "
                "does not contain a "
                "company identifier: "
                f"{career_url}"
            )

        return parts[0]

    @staticmethod
    def _extract_employment_type(
        value,
    ) -> str:

        if not value:
            return "Unknown"

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        if isinstance(
            value,
            dict,
        ):

            #
            # SmartRecruiters may represent
            # employment type as an object.
            #

            for key in (
                "label",
                "name",
                "value",
                "id",
            ):

                candidate = (
                    value.get(key)
                )

                if isinstance(
                    candidate,
                    str,
                ) and candidate.strip():

                    return candidate.strip()

        return "Unknown"

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        identifier = (
            self._extract_company_identifier(
                career_url
            )
        )

        endpoint = (
            self.API_URL.format(
                company=identifier
            )
        )

        jobs = []

        offset = 0

        for _ in range(
            self.max_pages
        ):

            response = self.http.get(
                endpoint,
                params={
                    "limit":
                        self.PAGE_SIZE,
                    "offset":
                        offset,
                },
                headers={
                    "Accept":
                        "application/json",
                },
            )

            payload = response.json()

            content = payload.get(
                "content",
                [],
            )

            if not content:
                break

            for item in content:

                location_data = (
                    item.get(
                        "location"
                    )
                    or {}
                )

                #
                # SmartRecruiters provides a structured
                # country code such as:
                #
                # us -> United States
                # in -> India
                # it -> Italy
                # jp -> Japan
                #
                # Preserve it so JobClassifier does not
                # need to guess from city/state text.
                #

                country_code = (
                    location_data.get(
                        "country"
                    )
                    or ""
                )

                country_code = (
                    str(country_code)
                    .strip()
                    .lower()
                )

                location_parts = [
                    location_data.get(
                        "city"
                    ),
                    location_data.get(
                        "region"
                    ),
                    location_data.get(
                        "country"
                    ),
                ]

                location = ", ".join(
                    part
                    for part
                    in location_parts
                    if part
                )

                if not location:
                    location = "Unknown"

                job_id = str(
                    item.get("id")
                    or ""
                )

                job_url = (
                    item.get(
                        "ref"
                    )
                    or ""
                )

                if not job_url:

                    job_url = (
                        "https://jobs."
                        "smartrecruiters.com/"
                        f"{identifier}/"
                        f"{job_id}"
                    )

                job = Job(
                    company=company,
                    title=(
                        item.get("name")
                        or "Unknown"
                    ).strip(),
                    url=job_url,
                    job_id=job_id,
                    location=location,
                    country="",
                    work_mode="Unknown",
                    job_type=self._extract_employment_type(
                        item.get(
                            "typeOfEmployment"
                        )
                    ),
                    experience_level=(
                        "Unknown"
                    ),
                    ats_platform=(
                        "SmartRecruiters"
                    ),
                    keywords=[],
                    score=0,
                    date_posted=(
                        item.get(
                            "releasedDate"
                        )
                        or None
                    ),
                    description=None,
                )

                job.metadata.update(
                    {
                        "smartrecruiters_company":
                            identifier,

                        "smartrecruiters_id":
                            job_id,

                        "country_code":
                            country_code,
                    }
                )

                jobs.append(
                    job
                )

            total = int(
                payload.get(
                    "totalFound",
                    0,
                )
                or 0
            )

            offset += len(
                content
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

        identifier = (
            job.metadata.get(
                "smartrecruiters_company"
            )
        )

        job_id = (
            job.metadata.get(
                "smartrecruiters_id"
            )
        )

        if (
            not identifier
            or not job_id
        ):
            return job

        endpoint = (
            "https://api."
            "smartrecruiters.com/"
            "v1/companies/"
            f"{identifier}/postings/"
            f"{job_id}"
        )

        response = self.http.get(
            endpoint,
            headers={
                "Accept":
                    "application/json",
            },
        )

        payload = response.json()

        sections = payload.get(
            "jobAd",
            {},
        ).get(
            "sections",
            {}
        )

        text_parts = []

        for section in (
            sections.values()
        ):

            if not isinstance(
                section,
                dict,
            ):
                continue

            text = section.get(
                "text"
            )

            if text:
                text_parts.append(
                    text
                )

        job.description = " ".join(
            text_parts
        )

        return job