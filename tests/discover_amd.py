from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_client import HttpClient


URLS = [
    "https://careers.amd.com",
    "https://careers.amd.com/careers-home",
    "https://careers.amd.com/careers-home/jobs",
]


http = HttpClient(
    timeout=20,
    retries=2,
)


for url in URLS:

    print()
    print("=" * 100)
    print("REQUEST:")
    print(url)
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
        "HTML characters:",
        len(response.text),
    )

    soup = BeautifulSoup(
        response.text,
        "lxml",
    )

    # ----------------------------------
    # External URLs potentially related
    # to jobs / ATS / APIs
    # ----------------------------------

    candidates = set()

    for element in soup.find_all(
        ["a", "script", "iframe"],
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
                "icims",
                "api",
                "search",
                "requisition",
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

    # ----------------------------------
    # Look for endpoint-like strings
    # embedded in page source.
    # ----------------------------------

    patterns = [
        r'https?://[^"\'\s<>]+',
        r'["\']([^"\']*api[^"\']*)["\']',
        r'["\']([^"\']*jobs?[^"\']*)["\']',
        r'["\']([^"\']*search[^"\']*)["\']',
    ]

    source_matches = set()

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

            match = str(
                match
            ).strip()

            if not match:
                continue

            lower = match.lower()

            if any(
                term in lower
                for term in (
                    "icims",
                    "job",
                    "career",
                    "requisition",
                    "api",
                )
            ):

                source_matches.add(
                    match
                )

    print()
    print(
        "Interesting source strings:"
    )

    for value in sorted(
        source_matches
    ):

        #
        # Prevent huge embedded blobs from
        # flooding the console.
        #

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