from collectors.ashby import (
    AshbyCollector,
)


collector = AshbyCollector()


# Replace this URL with a verified
# Ashby company board when testing.
CAREER_URL = (
    "https://jobs.ashbyhq.com/"
    "example"
)


try:

    jobs = collector.collect(
        "Test Company",
        CAREER_URL,
    )

except Exception as exc:

    print(
        "Ashby request failed:"
    )

    print(exc)

else:

    print(
        f"Jobs returned: "
        f"{len(jobs)}"
    )

    for job in jobs[:5]:

        print(
            "-" * 60
        )

        print(
            "ID:",
            job.job_id,
        )

        print(
            "Title:",
            job.title,
        )

        print(
            "Location:",
            job.location,
        )

        print(
            "Posted:",
            job.date_posted,
        )

        print(
            "URL:",
            job.url,
        )