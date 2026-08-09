from __future__ import annotations

from utils.http_client import HttpClient


BASE_URL = (
    "https://intel.wd1."
    "myworkdayjobs.com"
)


#
# Likely external career-site names.
#
# We're testing these rather than
# guessing one into production config.
#

CANDIDATE_SITES = [
    "External",
    "Intel",
    "IntelExternal",
    "ExternalCareerSite",
]


http = HttpClient(
    timeout=20,
    retries=1,
)


for site in CANDIDATE_SITES:

    endpoint = (
        f"{BASE_URL}/wday/cxs/"
        f"intel/{site}/jobs"
    )

    print()
    print("=" * 100)

    print(
        "SITE:",
        site,
    )

    print(
        "ENDPOINT:",
        endpoint,
    )

    print("=" * 100)

    try:

        response = http.post(
            endpoint,
            json={
                "appliedFacets": {},
                "limit": 20,
                "offset": 0,
                "searchText": "",
            },
            headers={
                "Accept":
                    "application/json",
                "Content-Type":
                    "application/json",
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

    try:

        payload = response.json()

    except Exception:

        print(
            "Not JSON"
        )

        print(
            response.text[:1000]
        )

        continue

    print(
        "Keys:",
        list(
            payload.keys()
        ),
    )

    total = (
        payload.get(
            "total",
            0,
        )
    )

    postings = (
        payload.get(
            "jobPostings",
            [],
        )
    )

    print(
        "Total jobs:",
        total,
    )

    print(
        "First page:",
        len(postings),
    )

    print()

    for posting in postings[:5]:

        print(
            "-",
            posting.get(
                "title"
            ),
        )

        print(
            " ",
            posting.get(
                "locationsText"
            ),
        )

        print(
            " ",
            posting.get(
                "externalPath"
            ),
        )


http.close()