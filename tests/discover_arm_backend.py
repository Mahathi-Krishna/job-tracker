from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_client import HttpClient


URLS = [
    "https://careers.arm.com",
    "https://careers.arm.com/en/search-jobs",
]


http = HttpClient(
    timeout=20,
    retries=1,
)


for url in URLS:

    print()
    print("=" * 100)
    print("REQUEST:", url)
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
                "api",
                "search",
                "icims",
                "workday",
                "jibe",
                "phenom",
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

    print()
    print(
        "Interesting source strings:"
    )

    patterns = (
        r'https?://[^"\'\s<>]+',
        r'["\']([^"\']*/api/[^"\']*)["\']',
        r'["\']([^"\']*jobs?[^"\']*)["\']',
        r'["\']([^"\']*search[^"\']*)["\']',
    )

    matches = set()

    for pattern in patterns:

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
                    "job",
                    "career",
                    "api",
                    "search",
                    "icims",
                    "workday",
                    "jibe",
                    "phenom",
                )
            ):

                matches.add(
                    value
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