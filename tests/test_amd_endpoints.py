from __future__ import annotations

import json

from utils.http_client import HttpClient


BASE_URL = (
    "https://careers.amd.com"
)


ENDPOINTS = [
    (
        "/api/jobs",
        {},
    ),
    (
        "/api/jobs",
        {
            "page": 1,
        },
    ),
    (
        "/api/jobs",
        {
            "page": 1,
            "categories": "Engineering",
        },
    ),
    (
        "/jobs",
        {
            "page": 1,
            "categories": "Engineering",
        },
    ),
    (
        "/careers-home/jobs",
        {
            "page": 1,
            "categories": "Engineering",
        },
    ),
]


http = HttpClient(
    timeout=20,
    retries=1,
)


for path, params in ENDPOINTS:

    url = (
        BASE_URL
        + path
    )

    print()
    print("=" * 100)

    print(
        "URL:",
        url,
    )

    print(
        "Params:",
        params,
    )

    print("=" * 100)

    try:

        response = http.get(
            url,
            params=params,
            allow_redirects=True,
            headers={
                "Accept":
                    "application/json,"
                    "text/html,"
                    "*/*",
            },
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

    content_type = (
        response.headers.get(
            "Content-Type",
            "",
        )
    )

    print(
        "Content-Type:",
        content_type,
    )

    print(
        "Characters:",
        len(response.text),
    )

    print()

    #
    # Try JSON first.
    #

    try:

        payload = (
            response.json()
        )

    except Exception:

        payload = None

    if payload is not None:

        print(
            "JSON RESPONSE"
        )

        if isinstance(
            payload,
            dict,
        ):

            print(
                "Top-level keys:",
                list(
                    payload.keys()
                ),
            )

            #
            # Print a limited preview,
            # not the entire job inventory.
            #

            preview = json.dumps(
                payload,
                indent=2,
            )

            print(
                preview[:5000]
            )

        elif isinstance(
            payload,
            list,
        ):

            print(
                "List length:",
                len(payload),
            )

            preview = json.dumps(
                payload[:3],
                indent=2,
            )

            print(
                preview[:5000]
            )

        continue

    #
    # Otherwise preview HTML/text.
    #

    print(
        "TEXT/HTML RESPONSE"
    )

    preview = (
        response.text[:3000]
        .replace(
            "\r",
            " ",
        )
        .replace(
            "\n",
            " ",
        )
    )

    print(
        preview
    )


http.close()