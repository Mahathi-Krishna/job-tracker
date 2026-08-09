from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from utils.http_client import HttpClient


JOB_ID = "88877"

BASE_URL = (
    "https://careers.amd.com"
)

API_URL = (
    f"{BASE_URL}/api/jobs"
)

SEARCH_URL = (
    f"{BASE_URL}/careers-home/jobs"
)


http = HttpClient(
    timeout=20,
    retries=1,
)


# ============================================================
# 1. Find the complete API object for JOB_ID
# ============================================================

print("=" * 100)
print("API JOB OBJECT")
print("=" * 100)


response = http.get(
    API_URL,
    headers={
        "Accept":
            "application/json",
    },
)


payload = response.json()


matching_job = None


for item in payload.get(
    "jobs",
    [],
):

    data = (
        item.get("data")
        if isinstance(
            item,
            dict,
        )
        else None
    )

    if not isinstance(
        data,
        dict,
    ):
        continue

    candidate_id = str(
        data.get("req_id")
        or data.get("slug")
        or ""
    )

    if candidate_id == JOB_ID:

        matching_job = item

        break


if matching_job is None:

    print(
        f"Job {JOB_ID} not found "
        "in /api/jobs"
    )

else:

    print(
        json.dumps(
            matching_job,
            indent=2,
        )
    )


# ============================================================
# 2. Search HTML for the requisition
# ============================================================

print()
print("=" * 100)
print("SEARCH PAGE LINKS")
print("=" * 100)


response = http.get(
    SEARCH_URL,
    params={
        "keywords":
            "Design Verification Engineer",
    },
    allow_redirects=True,
)


print(
    "Final URL:",
    response.url,
)


soup = BeautifulSoup(
    response.text,
    "lxml",
)


found_links = set()


for anchor in soup.find_all(
    "a",
    href=True,
):

    href = anchor.get(
        "href",
        "",
    )

    text = anchor.get_text(
        " ",
        strip=True,
    )

    combined = (
        href
        + " "
        + text
    )

    if (
        JOB_ID in combined
        or
        "Design Verification"
        in combined
    ):

        found_links.add(
            (
                text,
                href,
            )
        )


for text, href in sorted(
    found_links
):

    print()

    print(
        "Text:",
        text,
    )

    print(
        "Href:",
        href,
    )


# ============================================================
# 3. Search raw source around JOB_ID
# ============================================================

print()
print("=" * 100)
print("RAW HTML CONTEXT")
print("=" * 100)


source = response.text


for match in re.finditer(
    JOB_ID,
    source,
):

    start = max(
        0,
        match.start() - 500,
    )

    end = min(
        len(source),
        match.end() + 500,
    )

    print()

    print(
        source[
            start:end
        ]
    )

    print()
    print("-" * 100)


http.close()