from utils.http_client import (
    HttpClient,
)


ENDPOINT = (
    "https://qualcomm.wd12."
    "myworkdayjobs.com/"
    "wday/cxs/qualcomm/"
    "External/jobs"
)


http = HttpClient(
    timeout=20,
    retries=1,
)


response = http.post(
    ENDPOINT,
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


payload = response.json()


print(
    "Status:",
    response.status_code,
)

print(
    "Keys:",
    list(
        payload.keys()
    ),
)

print(
    "Total:",
    payload.get(
        "total"
    ),
)


postings = (
    payload.get(
        "jobPostings",
        []
    )
)


print(
    "First page:",
    len(postings),
)

print()


for posting in postings:

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