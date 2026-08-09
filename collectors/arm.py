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

        self.title_filter = None

    def set_title_filter(
        self,
        title_filter,
    ) -> None:

        self.title_filter = (
            title_filter
        )

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
        # Arm/Radancy URLs look like:
        #
        # /job/austin/title/
        # 33099/97584421536
        #
        # 33099 = organization ID
        # final number = posting ID
        #

        match = re.search(
            r"/(\d{6,})(?:[/?#]|$)",
            url.rstrip("/"),
        )

        numbers = re.findall(
            r"/(\d+)",
            url.rstrip("/"),
        )

        if numbers:

            return numbers[-1]

        if match:

            return match.group(1)

        return ""

    @classmethod
    def _extract_location(
        cls,
        card,
        title: str,
    ) -> str:

        #
        # Prefer explicit location elements.
        #

        location_selectors = (
            ".job-card__location",
            ".job-location",
            ".location",
            "[class*='location']",
        )

        for selector in (
            location_selectors
        ):

            element = card.select_one(
                selector
            )

            if element:

                value = cls._clean(
                    element.get_text(
                        " ",
                        strip=True,
                    )
                )

                if value:

                    return value

        #
        # Fall back to card text, but strip
        # the title and common category/
        # description elements first.
        #

        card_copy = BeautifulSoup(
            str(card),
            "lxml",
        )

        for element in (
            card_copy.select(
                ".job-card__title,"
                ".job-card__intro,"
                ".content-description,"
                "button,"
                "a"
            )
        ):

            element.decompose()

        value = cls._clean(
            card_copy.get_text(
                " ",
                strip=True,
            )
        )

        if value:

            return value

        return "Unknown"

    def _page_url(
        self,
        page: int,
    ) -> str:

        if page <= 1:

            return self.SEARCH_URL

        #
        # Arm/TalentBrew exposes pagination
        # as:
        #
        # /search-jobs&p=2
        #

        return (
            f"{self.SEARCH_URL}"
            f"&p={page}"
        )

    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:

        jobs = []

        seen_urls = set()

        previous_urls = None

        for page in range(
            1,
            self.max_pages + 1,
        ):

            page_url = (
                self._page_url(
                    page
                )
            )

            response = self.http.get(
                page_url,
                allow_redirects=True,
            )

            soup = BeautifulSoup(
                response.text,
                "lxml",
            )

            #
            # Arm explicitly marks individual
            # results with job-card.
            #

            cards = soup.select(
                ".job-card"
            )

            if not cards:

                break

            current_urls = set()

            for card in cards:

                anchor = card.select_one(
                    "a[href*='/job/']"
                )

                if anchor is None:
                    continue

                href = (
                    anchor.get(
                        "href",
                        "",
                    )
                    .strip()
                )

                if not href:
                    continue

                url = urljoin(
                    response.url,
                    href,
                )

                current_urls.add(
                    url
                )

                if url in seen_urls:
                    continue

                title_element = (
                    card.select_one(
                        ".job-card__title"
                    )
                )

                if title_element:

                    title = self._clean(
                        title_element.get_text(
                            " ",
                            strip=True,
                        )
                    )

                else:

                    title = self._clean(
                        anchor.get_text(
                            " ",
                            strip=True,
                        )
                    )

                if not title:
                    continue

                if (
                    self.title_filter
                    is not None
                    and not
                    self.title_filter.matches(
                        title
                    )
                ):

                    seen_urls.add(
                        url
                    )

                    continue

                job_id = (
                    self._extract_job_id(
                        url
                    )
                )

                location = (
                    self._extract_location(
                        card,
                        title,
                    )
                )

                job = Job(
                    company=company,
                    title=title,
                    url=url,
                    job_id=job_id,
                    location=location,
                    country="",
                    work_mode="Unknown",
                    job_type="Unknown",
                    experience_level=(
                        "Unknown"
                    ),
                    ats_platform=(
                        "Arm Radancy"
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

            #
            # Defensive pagination stop.
            #
            # If another page gives exactly
            # the same posting URLs, the
            # pagination parameter wasn't
            # honored. Stop instead of
            # requesting 50 copies.
            #

            if (
                previous_urls is not None
                and current_urls
                == previous_urls
            ):

                break

            previous_urls = (
                current_urls
            )

            if not current_urls:
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

        #
        # Try likely job-description
        # containers first.
        #

        selectors = (
            ".job-description",
            ".job-description__content",
            ".job-detail",
            "[class*='job-description']",
        )

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if element:

                description = (
                    self._clean(
                        element.get_text(
                            " ",
                            strip=True,
                        )
                    )
                )

                if description:

                    job.description = (
                        description
                    )

                    return job

        #
        # Conservative fallback.
        #

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

        job.description = self._clean(
            soup.get_text(
                " ",
                strip=True,
            )
        )

        return job