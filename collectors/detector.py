from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from utils.http_client import HttpClient
from utils.logger import logger


@dataclass(slots=True)
class ATSDetectionResult:
    ats: str
    url: str
    detected_by: str


class ATSDetector:

    ATS_DOMAINS = {
        "greenhouse": (
            "greenhouse.io",
            "greenhouse.com",
        ),
        "lever": (
            "lever.co",
        ),
        "workday": (
            "myworkdayjobs.com",
        ),
        "ashby": (
            "ashbyhq.com",
        ),
        "smartrecruiters": (
            "smartrecruiters.com",
        ),
        "icims": (
            "icims.com",
        ),
        "oracle": (
            "oraclecloud.com",
        ),
        "successfactors": (
            "successfactors.com",
            "successfactors.eu",
        ),
    }

    def __init__(
        self,
        timeout: int = 12,
        max_html_chars: int = 1_000_000,
    ):

        self.http = HttpClient(
            timeout=timeout,
            retries=2,
        )

        self.max_html_chars = max_html_chars

    @classmethod
    def detect_from_url(
        cls,
        url: str,
    ) -> str | None:

        hostname = (
            urlparse(url)
            .netloc
            .lower()
        )

        for ats, domains in (
            cls.ATS_DOMAINS.items()
        ):

            for domain in domains:

                if domain in hostname:
                    return ats

        return None

    @staticmethod
    def normalize_url(
        ats: str,
        url: str,
    ) -> str:

        if ats == "greenhouse":

            parsed = urlparse(url)

            path_parts = [
                part
                for part in parsed.path.split("/")
                if part
            ]

            #
            # Greenhouse commonly exposes:
            #
            # /company
            # /company/jobs/123
            #
            # We only want the company board.
            #

            if path_parts:

                board = path_parts[0]

                return (
                    f"{parsed.scheme}://"
                    f"{parsed.netloc}/"
                    f"{board}"
                )

        if ats == "smartrecruiters":

            parsed = urlparse(url)

            path_parts = [
                part
                for part in parsed.path.split("/")
                if part
            ]

            #
            # careers.smartrecruiters.com/Company
            #

            if (
                "careers.smartrecruiters.com"
                in parsed.netloc.lower()
                and path_parts
            ):

                return (
                    "https://careers."
                    "smartrecruiters.com/"
                    f"{path_parts[0]}"
                )

        return url

    def detect(
        self,
        career_url: str,
    ) -> ATSDetectionResult:

        direct = self.detect_from_url(
            career_url
        )

        if direct:

            return ATSDetectionResult(
                ats=direct,
                url=self.normalize_url(
                    direct,
                    career_url,
                ),
                detected_by="url",
            )

        try:

            response = self.http.get(
                career_url,
                allow_redirects=True,
            )

        except Exception as exc:

            logger.warning(
                "ATS discovery failed for "
                f"{career_url}: {exc}"
            )

            return ATSDetectionResult(
                ats="generic",
                url=career_url,
                detected_by="failed",
            )

        final_url = response.url

        redirected = (
            self.detect_from_url(
                final_url
            )
        )

        if redirected:

            return ATSDetectionResult(
                ats=redirected,
                url=self.normalize_url(
                    redirected,
                    final_url,
                ),
                detected_by="redirect",
            )

        content_type = (
            response.headers.get(
                "Content-Type",
                "",
            ).lower()
        )

        if "html" not in content_type:

            return ATSDetectionResult(
                ats="generic",
                url=final_url,
                detected_by="unknown",
            )

        page_html = response.text[
            :self.max_html_chars
        ]

        detected = (
            self._detect_from_html(
                page_html,
                final_url,
            )
        )

        if detected:
            return detected

        return ATSDetectionResult(
            ats="generic",
            url=final_url,
            detected_by="unknown",
        )

    def _detect_from_html(
        self,
        page_html: str,
        base_url: str,
    ) -> ATSDetectionResult | None:

        candidates = re.findall(
            r"""(?:href|src)\s*=\s*["']([^"']+)["']""",
            page_html,
            flags=re.IGNORECASE,
        )

        candidates.extend(
            re.findall(
                r"""https?://[^\s"'<>\\]+""",
                page_html,
                flags=re.IGNORECASE,
            )
        )

        #
        # Prefer useful careers URLs over
        # random JS/assets/login links.
        #

        scored_candidates = []

        for candidate in candidates:

            candidate = candidate.replace(
                "&amp;",
                "&",
            )

            absolute_url = urljoin(
                base_url,
                candidate,
            )

            ats = self.detect_from_url(
                absolute_url
            )

            if not ats:
                continue

            score = 0

            lower = absolute_url.lower()

            if "/jobs" in lower:
                score += 10

            if "/careers" in lower:
                score += 10

            if "job-boards." in lower:
                score += 10

            if "boards." in lower:
                score += 10

            if "/search" in lower:
                score += 5

            #
            # Strongly penalize things that
            # aren't actual career boards.
            #

            if "/login" in lower:
                score -= 50

            #
            # Assets are not career endpoints.
            # Never allow them to become the
            # resolved ATS URL.
            #

            asset_extensions = (
                ".js",
                ".css",
                ".png",
                ".jpg",
                ".jpeg",
                ".svg",
                ".gif",
                ".woff",
                ".woff2",
            )

            clean_path = (
                urlparse(
                    absolute_url
                )
                .path
                .lower()
            )

            if clean_path.endswith(
                asset_extensions
            ):
                continue

            if "/static/" in lower:
                continue

            scored_candidates.append(
                (
                    score,
                    ats,
                    absolute_url,
                )
            )

        if not scored_candidates:
            return None

        scored_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        score, ats, url = (
            scored_candidates[0]
        )

        if score < 0:
            return None

        return ATSDetectionResult(
            ats=ats,
            url=self.normalize_url(
                ats,
                url,
            ),
            detected_by="html",
        )

    def close(
        self,
    ) -> None:

        self.http.close()