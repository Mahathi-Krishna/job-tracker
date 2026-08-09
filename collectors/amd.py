from __future__ import annotations

import html
import re

from collectors.base import BaseCollector
from models.job import Job
from utils.http_client import HttpClient


class AMDCollector(BaseCollector):

    API_URL = (
        "https://careers.amd.com/api/jobs"
    )

    PUBLIC_BASE = (
        "https://careers.amd.com/"
        "careers-home/job/"
    )

    def __init__(
        self,
        timeout: int = 20,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=2,
        )

        self.title_filter = None

    def set_title_filter(
        self,
        title_filter,
    ) -> None:

        self.title_filter = (
            title_filter
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

    @staticmethod
    def _get_data(
        item: dict,
    ) -> dict:

        data = item.get(
            "data"
        )

        if isinstance(
            data,
            dict,
        ):
            return data

        return item

    @staticmethod
    def _extract_location(
        data: dict,
    ) -> str:

        #
        # Jibe installations can represent
        # location differently, so check
        # several common fields.
        #

        for key in (
            "full_location",
            "short_location",
            "location",
            "location_name",
            "city_state_country",
        ):

            value = data.get(
                key
            )

            if isinstance(
                value,
                str,
            ) and value.strip():

                return value.strip()

        locations = data.get(
            "locations"
        )

        if isinstance(
            locations,
            list,
        ):

            parts = []

            for location in locations:

                if isinstance(
                    location,
                    str,
                ):

                    if location.strip():
                        parts.append(
                            location.strip()
                        )

                elif isinstance(
                    location,
                    dict,
                ):

                    text_parts = []

                    for key in (
                        "city",
                        "state",
                        "country",
                    ):

                        value = (
                            location.get(
                                key
                            )
                        )

                        if (
                            isinstance(
                                value,
                                str,
                            )
                            and value.strip()
                        ):

                            text_parts.append(
                                value.strip()
                            )

                    if text_parts:

                        parts.append(
                            ", ".join(
                                text_parts
                            )
                        )

            if parts:

                return "; ".join(
                    parts
                )

        return "Unknown"

    @classmethod
    def _extract_url(
        cls,
        data: dict,
        job_id: str,
    ) -> str:

        metadata = (
            data.get(
                "meta_data"
            )
            or {}
        )

        if isinstance(
            metadata,
            dict,
        ):

            canonical_url = (
                metadata.get(
                    "canonical_url"
                )
            )

            if (
                isinstance(
                    canonical_url,
                    str,
                )
                and canonical_url.strip()
            ):

                return (
                    canonical_url.strip()
                )

        canonical_url = (
            data.get(
                "canonical_url"
            )
        )

        if (
            isinstance(
                canonical_url,
                str,
            )
            and canonical_url.strip()
        ):

            return (
                canonical_url.strip()
            )

        return ""

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        response = self.http.get(
            self.API_URL,
            headers={
                "Accept":
                    "application/json",
            },
        )

        payload = response.json()

        raw_jobs = (
            payload.get(
                "jobs",
                []
            )
        )

        jobs = []

        for item in raw_jobs:

            if not isinstance(
                item,
                dict,
            ):
                continue

            data = self._get_data(
                item
            )

            title = str(
                data.get(
                    "title"
                )
                or ""
            ).strip()

            if not title:
                continue

            #
            # Same strategy as Workday:
            # cheap pre-filter first.
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

            job_id = str(
                data.get(
                    "req_id"
                )
                or data.get(
                    "slug"
                )
                or data.get(
                    "id"
                )
                or ""
            ).strip()

            description = (
                self._clean_html(
                    data.get(
                        "description"
                    )
                )
            )

            location = (
                self._extract_location(
                    data
                )
            )

            job_url = (
                self._extract_url(
                    data,
                    job_id,
                )
            )

            job = Job(
                company=company,
                title=title,
                url=job_url,
                job_id=job_id,
                location=location,
                country="",
                work_mode="Unknown",
                job_type=(
                    str(
                        data.get(
                            "employment_type"
                        )
                        or "Unknown"
                    )
                    .replace(
                        "_",
                        " ",
                    )
                    .title()
                ),
                experience_level=(
                    "Unknown"
                ),
                ats_platform=(
                    "AMD Jibe"
                ),
                keywords=[],
                score=0,
                date_posted=(
                    data.get(
                        "posted_date"
                    )
                    or data.get(
                        "date_posted"
                    )
                    or data.get(
                        "posted"
                    )
                    or None
                ),
                description=description,
            )

            country_code = (
                data.get(
                    "country_code"
                )
                or ""
            )

            country_code = (
                str(country_code)
                .strip()
                .lower()
            )


            if country_code:

                job.metadata[
                    "country_code"
                ] = country_code

            jobs.append(
                job
            )

        return jobs

    def enrich(
        self,
        job: Job,
    ) -> Job:

        #
        # /api/jobs already provides the
        # description, so no additional
        # request is necessary.
        #

        return job