from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_client import HttpClient


URLS = [
    "https://careers.qualcomm.com",
    "https://www.qualcomm.com/company/careers",
]


http = HttpClient(
    timeout=20,
    retries=2,
)


for url in URLS:

    print()
    print("=" * 100)

    print(
        "REQUEST:",
        url,
    )

    print("=" * 100)

    try:

        response = http.get(
            url,
            allow_redirects=True,
        )

    except Exception as exc:

        print(
            "FAILED:",
            type(exc).__name__,
            exc,
        )

        continue

    print(
        "Status:",
        response.status_code,
    )

    print(
        "Final URL:",
        response.url,
    )

    print(
        "Content-Type:",
        response.headers.get(
            "Content-Type",
            "",
        ),
    )

    print(
        "Characters:",
        len(response.text),
    )

    soup = BeautifulSoup(
        response.text,
        "lxml",
    )

    candidates = set()

    for element in soup.find_all(
        [
            "a",
            "script",
            "iframe",
        ]
    ):

        value = (
            element.get("href")
            or element.get("src")
        )

        if not value:
            continue

        absolute = urljoin(
            response.url,
            value,
        )

        lower = absolute.lower()

        if any(
            term in lower
            for term in (
                "job",
                "career",
                "workday",
                "icims",
                "greenhouse",
                "lever",
                "smartrecruiters",
                "api",
            )
        ):

            candidates.add(
                absolute
            )

    print()
    print(
        "Interesting URLs:"
    )

    for candidate in sorted(
        candidates
    ):

        print(
            "-",
            candidate,
        )

    #
    # Look for ATS/backend references
    # embedded directly in HTML.
    #

    source_patterns = (
        r'https?://[^"\'\s<>]+',
        r'["\']([^"\']*workday[^"\']*)["\']',
        r'["\']([^"\']*myworkdayjobs[^"\']*)["\']',
        r'["\']([^"\']*icims[^"\']*)["\']',
        r'["\']([^"\']*/api/[^"\']*)["\']',
    )

    matches = set()

    for pattern in source_patterns:

        for match in re.findall(
            pattern,
            response.text,
            flags=re.IGNORECASE,
        ):

            if isinstance(
                match,
                tuple,
            ):

                match = "".join(
                    match
                )

            value = str(
                match
            ).strip()

            if not value:
                continue

            lower = value.lower()

            if any(
                term in lower
                for term in (
                    "workday",
                    "myworkdayjobs",
                    "icims",
                    "job",
                    "career",
                )
            ):

                matches.add(
                    value
                )

    print()
    print(
        "Interesting source strings:"
    )

    for value in sorted(
        matches
    ):

        if len(value) > 300:

            value = (
                value[:300]
                + "..."
            )

        print(
            "-",
            value,
        )


http.close()