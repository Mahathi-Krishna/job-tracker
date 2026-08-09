import time

from collectors.synopsys import (
    SynopsysCollector,
)


collector = SynopsysCollector()


started = time.monotonic()


jobs = collector.collect(
    "Synopsys",
    (
        "https://careers."
        "synopsys.com/search-jobs"
    ),
)


elapsed = (
    time.monotonic()
    - started
)


print(
    "Jobs returned:",
    len(jobs),
)

print(
    "Collection time:",
    f"{elapsed:.1f} seconds",
)

print()


for job in jobs[:30]:

    print("-" * 70)

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