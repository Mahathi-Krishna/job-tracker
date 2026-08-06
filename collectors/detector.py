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
    """
    Lightweight ATS detector.

    Detection order:

    1. Inspect the configured URL itself.
    2. Follow normal HTTP redirects.
    3. Inspect a limited amount of returned HTML for ATS URLs.

    No browser or JavaScript engine is used.
    """

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

        hostname = urlparse(
            url
        ).netloc.lower()

        for ats, domains in cls.ATS_DOMAINS.items():

            for domain in domains:

                if domain in hostname:
                    return ats

        return None

    def detect(
        self,
        career_url: str,
    ) -> ATSDetectionResult:

        # --------------------------------
        # 1. Direct URL
        # --------------------------------

        direct = self.detect_from_url(
            career_url
        )

        if direct:

            return ATSDetectionResult(
                ats=direct,
                url=career_url,
                detected_by="url",
            )

        # --------------------------------
        # 2. Fetch careers page
        # --------------------------------

        try:

            response = self.http.get(
                career_url,
                allow_redirects=True,
            )

        except Exception as exc:

            logger.warning(
                f"ATS discovery failed for "
                f"{career_url}: {exc}"
            )

            return ATSDetectionResult(
                ats="generic",
                url=career_url,
                detected_by="failed",
            )

        final_url = response.url

        # --------------------------------
        # 3. Redirect destination
        # --------------------------------

        redirected = self.detect_from_url(
            final_url
        )

        if redirected:

            return ATSDetectionResult(
                ats=redirected,
                url=final_url,
                detected_by="redirect",
            )

        # --------------------------------
        # 4. HTML inspection
        # --------------------------------

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "html" not in content_type:

            return ATSDetectionResult(
                ats="generic",
                url=final_url,
                detected_by="unknown",
            )

        html = response.text[
            : self.max_html_chars
        ]

        detected = self._detect_from_html(
            html,
            final_url,
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
        html: str,
        base_url: str,
    ) -> ATSDetectionResult | None:

        # Extract URLs from href/src attributes.
        candidates = re.findall(
            r"""(?:href|src)\s*=\s*["']([^"']+)["']""",
            html,
            flags=re.IGNORECASE,
        )

        # Also search raw HTML because some ATS
        # addresses appear inside JavaScript/config.
        candidates.extend(
            re.findall(
                r"""https?://[^\s"'<>\\]+""",
                html,
                flags=re.IGNORECASE,
            )
        )

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

            if ats:

                return ATSDetectionResult(
                    ats=ats,
                    url=absolute_url,
                    detected_by="html",
                )

        return None

    def close(self) -> None:
        self.http.close()